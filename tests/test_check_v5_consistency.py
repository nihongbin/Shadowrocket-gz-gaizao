from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-v5-consistency.py"
PRIVATE_V5 = ROOT / "local" / "private-configs" / "S1-default-lazy-proxy-doh-1-stable-enhanced-cnapp-v5.conf"
PUBLIC_S5 = ROOT / "configs" / "S5-scenario-cn-us-v5-mvp-v0.conf"


def load_checker():
    if not SCRIPT.exists():
        raise AssertionError("expected V5 consistency checker to exist")
    spec = importlib.util.spec_from_file_location("check_v5_consistency", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load V5 consistency checker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(PRIVATE_V5.exists(), "private V5 baseline is local-only")
class CheckV5ConsistencyTests(unittest.TestCase):
    def test_private_and_public_effective_sections_match(self) -> None:
        checker = load_checker()
        result = checker.compare_effective_sections(
            PRIVATE_V5.read_text(encoding="utf-8-sig"),
            PUBLIC_S5.read_text(encoding="utf-8-sig"),
        )
        self.assertEqual(result, {"General": True, "Rule": True, "Host": True})

    def test_rule_difference_is_detected(self) -> None:
        checker = load_checker()
        private = PRIVATE_V5.read_text(encoding="utf-8-sig")
        public = PUBLIC_S5.read_text(encoding="utf-8-sig").replace(
            "FINAL,PROXY", "FINAL,DIRECT", 1
        )
        result = checker.compare_effective_sections(private, public)
        self.assertFalse(result["Rule"])

    def test_governed_ruleset_url_is_equivalent_to_locked_upstream_identity(self) -> None:
        checker = load_checker()
        private = PRIVATE_V5.read_text(encoding="utf-8-sig")
        upstream = (
            "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/"
            "rule/Shadowrocket/YouTube/YouTube.list"
        )
        governed = (
            "https://raw.githubusercontent.com/nihongbin/Shadowrocket-gz-gaizao/"
            "main/rulesets/v5/youtube.list"
        )
        public = private.replace(upstream, governed, 1)

        result = checker.compare_effective_sections(private, public)

        self.assertTrue(result["Rule"])


if __name__ == "__main__":
    unittest.main()
