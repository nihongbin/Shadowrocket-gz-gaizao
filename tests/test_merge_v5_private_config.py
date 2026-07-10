from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "merge-v5-private-config.py"
TEMPLATE = ROOT / "configs" / "S5-scenario-cn-us-v5-mvp-v0.conf"


def load_merger():
    if not SCRIPT.exists():
        raise AssertionError("expected V5 merger script to exist")
    spec = importlib.util.spec_from_file_location("merge_v5_private", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load V5 merger")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALID_BASE = """[General]
ipv6 = false

[Proxy]
node-a = custom, example.invalid, 443

[Proxy Group]
PROXY = select, node-a

[URL Rewrite]
^https://example.invalid reject

[Rule]
FINAL,DIRECT
"""


class MergeV5PrivateConfigTests(unittest.TestCase):
    def test_merge_rejects_base_without_private_proxy_sections(self) -> None:
        merger = load_merger()
        template = TEMPLATE.read_text(encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "Proxy"):
            merger.merge_configs("[General]\nipv6 = false\n", template)

    def test_merge_rejects_base_without_proxy_policy_group(self) -> None:
        merger = load_merger()
        template = TEMPLATE.read_text(encoding="utf-8")
        base = VALID_BASE.replace("PROXY = select, node-a", "US-NODES = select, node-a")

        with self.assertRaisesRegex(ValueError, "PROXY"):
            merger.merge_configs(base, template)

    def test_merge_keeps_only_private_proxy_sections_and_v5_logic(self) -> None:
        merger = load_merger()
        template = TEMPLATE.read_text(encoding="utf-8")
        merged = merger.merge_configs(VALID_BASE, template)
        _, sections = merger.parse_config(merged)

        self.assertIn("Proxy", sections)
        self.assertIn("Proxy Group", sections)
        self.assertNotIn("URL Rewrite", sections)
        self.assertNotIn("MITM", sections)
        self.assertEqual(merger.last_effective_rule(merged), "FINAL,PROXY")

    def test_output_path_is_limited_to_local_private_configs(self) -> None:
        merger = load_merger()
        allowed = ROOT / "local" / "private-configs" / "merged.conf"
        self.assertEqual(merger.validate_output_path(allowed), allowed.resolve())

        with tempfile.TemporaryDirectory() as temp_dir:
            outside = Path(temp_dir) / "merged.conf"
            with self.assertRaisesRegex(ValueError, "local/private-configs"):
                merger.validate_output_path(outside)

        with self.assertRaisesRegex(ValueError, "local/private-configs"):
            merger.validate_output_path(ROOT / "configs" / "private.conf")


if __name__ == "__main__":
    unittest.main()
