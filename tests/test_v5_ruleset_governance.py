from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "scripts" / "v5_rulesets.py"
REGISTRY = ROOT / "references" / "v5-mvp" / "ruleset-sources.json"


def load_rulesets():
    if not LIBRARY.exists():
        raise AssertionError("expected V5 ruleset governance library to exist")
    spec = importlib.util.spec_from_file_location("v5_rulesets", LIBRARY)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load V5 ruleset governance library")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class V5RulesetSemanticTests(unittest.TestCase):
    def test_comments_order_and_duplicates_do_not_change_semantic_hash(self) -> None:
        rulesets = load_rulesets()
        first = """# UPDATED: today
DOMAIN-SUFFIX,example.com
IP-CIDR,203.0.113.0/24,no-resolve
DOMAIN-SUFFIX,example.com
"""
        second = """# UPDATED: tomorrow
IP-CIDR,203.0.113.0/24,no-resolve

DOMAIN-SUFFIX,example.com
"""

        self.assertEqual(rulesets.canonical_rules(first), rulesets.canonical_rules(second))
        self.assertEqual(rulesets.semantic_sha256(first), rulesets.semantic_sha256(second))

    def test_real_rule_change_reports_added_and_removed_rules(self) -> None:
        rulesets = load_rulesets()
        before = "DOMAIN-SUFFIX,old.example\nDOMAIN-SUFFIX,keep.example\n"
        after = "DOMAIN-SUFFIX,new.example\nDOMAIN-SUFFIX,keep.example\n"

        result = rulesets.diff_rule_text(before, after)

        self.assertEqual(result["added"], ["DOMAIN-SUFFIX,new.example"])
        self.assertEqual(result["removed"], ["DOMAIN-SUFFIX,old.example"])

    def test_snapshot_render_is_stable_and_carries_gpl_attribution(self) -> None:
        rulesets = load_rulesets()
        entry = {
            "id": "demo",
            "name": "Demo/Demo",
            "policy": "PROXY",
            "upstream_url": "https://example.invalid/Demo.list",
            "snapshot_path": "rulesets/v5/demo.list",
            "public_url": rulesets.governed_public_url("demo"),
        }
        upstream = "# UPDATED: unstable metadata\nDOMAIN-SUFFIX,b.example\nDOMAIN-SUFFIX,a.example\n"

        first = rulesets.render_snapshot(entry, upstream)
        second = rulesets.render_snapshot(entry, upstream)

        self.assertEqual(first, second)
        self.assertIn("GPL-2.0", first)
        self.assertIn("https://example.invalid/Demo.list", first)
        self.assertNotIn("UPDATED: unstable metadata", first)
        self.assertLess(first.index("DOMAIN-SUFFIX,a.example"), first.index("DOMAIN-SUFFIX,b.example"))

    def test_sync_updates_snapshot_and_registry_without_runtime_timestamp(self) -> None:
        rulesets = load_rulesets()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            entry = {
                "id": "demo",
                "name": "Demo/Demo",
                "policy": "DIRECT",
                "upstream_url": "https://example.invalid/Demo.list",
                "snapshot_path": "rulesets/v5/demo.list",
                "public_url": rulesets.governed_public_url("demo"),
                "semantic_sha256": "0" * 64,
                "rule_count": 0,
                "license": "GPL-2.0",
            }
            registry = {
                "schema_version": 1,
                "repository": rulesets.REPOSITORY,
                "sources": [entry],
            }
            source_text = "DOMAIN-SUFFIX,example.cn\n"

            changed = rulesets.sync_registry_sources(
                root,
                registry,
                {"demo": source_text},
            )
            first_registry = rulesets.render_registry(registry)
            first_snapshot = (root / "rulesets" / "v5" / "demo.list").read_text(encoding="utf-8")
            changed_again = rulesets.sync_registry_sources(
                root,
                registry,
                {"demo": source_text},
            )

            self.assertEqual(changed, ["demo"])
            self.assertEqual(changed_again, [])
            self.assertEqual(first_registry, rulesets.render_registry(registry))
            self.assertNotRegex(first_registry, r"generated|updated_at|timestamp")
            self.assertIn("DOMAIN-SUFFIX,example.cn", first_snapshot)

    def test_source_fetch_retries_transient_failures_before_reporting_error(self) -> None:
        rulesets = load_rulesets()
        attempts = 0

        def flaky_fetcher(_url: str) -> str:
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise OSError("temporary TLS failure")
            return "DOMAIN-SUFFIX,example.com\n"

        registry = {
            "sources": [
                {
                    "id": "demo",
                    "upstream_url": "https://example.invalid/Demo.list",
                }
            ]
        }

        contents, errors = rulesets.fetch_registry_sources(
            registry,
            fetcher=flaky_fetcher,
            attempts=3,
            retry_delay_seconds=0,
        )

        self.assertEqual(attempts, 3)
        self.assertEqual(errors, {})
        self.assertIn("demo", contents)


class V5RulesetRepositoryTests(unittest.TestCase):
    def test_tracked_registry_and_snapshots_are_internally_consistent(self) -> None:
        rulesets = load_rulesets()
        self.assertTrue(REGISTRY.exists(), "expected governed source registry")
        registry = rulesets.load_registry(REGISTRY, ROOT)

        self.assertEqual(len(registry["sources"]), 33)
        self.assertEqual(rulesets.validate_snapshots(ROOT, registry), [])
        self.assertEqual(
            len({entry["id"] for entry in registry["sources"]}),
            len(registry["sources"]),
        )

    def test_public_manifests_use_only_governed_snapshot_urls(self) -> None:
        rulesets = load_rulesets()
        registry = rulesets.load_registry(REGISTRY, ROOT)
        governed_urls = {entry["public_url"] for entry in registry["sources"]}
        lazy_text = (ROOT / "references" / "v5-mvp" / "lazy-body-rules.txt").read_text(
            encoding="utf-8"
        )
        ruleset_urls = {
            line.split(",", 2)[1]
            for line in lazy_text.splitlines()
            if line.strip().startswith("RULE-SET,")
        }

        self.assertEqual(ruleset_urls, governed_urls)
        self.assertNotIn("blackmatrix7/ios_rule_script/master", lazy_text)

    def test_monitor_detects_snapshot_drift_separately_from_upstream_change(self) -> None:
        rulesets = load_rulesets()
        source_text = "DOMAIN-SUFFIX,expected.example\n"
        semantic_hash = rulesets.semantic_sha256(source_text)
        entry = {
            "id": "demo",
            "name": "Demo/Demo",
            "policy": "PROXY",
            "upstream_url": "https://example.invalid/Demo.list",
            "snapshot_path": "rulesets/v5/demo.list",
            "public_url": rulesets.governed_public_url("demo"),
            "semantic_sha256": semantic_hash,
            "rule_count": 1,
            "license": "GPL-2.0",
        }

        upstream_change = rulesets.analyze_source(entry, source_text + "DOMAIN-SUFFIX,new.example\n", source_text)
        snapshot_drift = rulesets.analyze_source(entry, source_text, "DOMAIN-SUFFIX,wrong.example\n")

        self.assertEqual(upstream_change["status"], "CHANGED")
        self.assertEqual(snapshot_drift["status"], "SNAPSHOT_DRIFT")


if __name__ == "__main__":
    unittest.main()
