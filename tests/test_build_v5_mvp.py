from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build-v5-mvp-template.py"
TEMPLATE = ROOT / "configs" / "S5-scenario-cn-us-v5-mvp-v0.conf"
PRIVATE_V5 = ROOT / "local" / "private-configs" / "S1-default-lazy-proxy-doh-1-stable-enhanced-cnapp-v5.conf"
MANIFEST_DIR = ROOT / "references" / "v5-mvp"


def load_builder():
    spec = importlib.util.spec_from_file_location("build_v5_mvp", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load V5 builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BuildV5MvpTests(unittest.TestCase):
    def test_manifest_revision_includes_governed_ruleset_registry(self) -> None:
        builder = load_builder()

        self.assertIn("ruleset-sources.json", builder.MANIFEST_BUILD_INPUTS)

    def test_public_template_uses_only_governed_ruleset_urls(self) -> None:
        text = TEMPLATE.read_text(encoding="utf-8")

        self.assertIn(
            "raw.githubusercontent.com/nihongbin/Shadowrocket-gz-gaizao/main/rulesets/v5/",
            text,
        )
        self.assertNotIn("blackmatrix7/ios_rule_script/master", text)

    @unittest.skipUnless(PRIVATE_V5.exists(), "private V5 baseline is local-only")
    def test_manifest_resync_preserves_governed_urls_and_maintenance_docs(self) -> None:
        builder = load_builder()
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_dir = Path(temp_dir) / "v5-mvp"
            shutil.copytree(MANIFEST_DIR, manifest_dir)

            builder.extract_manifests(PRIVATE_V5, manifest_dir)

            lazy = (manifest_dir / "lazy-body-rules.txt").read_text(encoding="utf-8")
            readme = (manifest_dir / "README.md").read_text(encoding="utf-8")
            self.assertNotIn("blackmatrix7/ios_rule_script/master", lazy)
            self.assertIn("ruleset-sources.json", readme)
            self.assertIn("manage-v5-rulesets.py validate", readme)

    def test_check_fails_when_output_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing.conf"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--check", "--output", str(missing)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("missing", (result.stdout + result.stderr).lower())

    def test_validator_rejects_unsafe_public_values(self) -> None:
        builder = load_builder()
        original = TEMPLATE.read_text(encoding="utf-8")
        unsafe_variants = {
            "subscription": original.replace(
                "[General]\n",
                "[General]\nsubscription-url = https://example.invalid/private-feed\n",
                1,
            ),
            "api-key": original.replace(
                "[General]\n",
                "[General]\napi-key = example-private-value\n",
                1,
            ),
            "system-dns": original.replace(
                "dns-server = https://cloudflare-dns.com/dns-query#proxy, https://security.cloudflare-dns.com/dns-query#proxy",
                "dns-server = system",
                1,
            ),
            "ipv6": original.replace("ipv6 = false", "ipv6 = true", 1),
            "system-host": original.replace(
                "wechat.com = server:119.29.29.29",
                "wechat.com = server:system",
                1,
            ),
        }

        for name, content in unsafe_variants.items():
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    builder.validate_public_template(content)


if __name__ == "__main__":
    unittest.main()
