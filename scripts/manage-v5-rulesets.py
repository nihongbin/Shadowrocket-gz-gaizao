#!/usr/bin/env python3
"""Bootstrap, validate, monitor, and update governed V5 RULE-SET snapshots."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import v5_rulesets as rulesets


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / rulesets.REGISTRY_RELATIVE_PATH
REMOTE_RULESETS_PATH = ROOT / "references" / "v5-mvp" / "remote-rulesets.csv"


def write_github_outputs(path: str | None, values: dict[str, object]) -> None:
    if not path:
        return
    with Path(path).open("a", encoding="utf-8", newline="\n") as handle:
        for key, value in values.items():
            if isinstance(value, bool):
                rendered = str(value).lower()
            elif isinstance(value, list):
                rendered = ",".join(str(item) for item in value)
            else:
                rendered = str(value)
            handle.write(f"{key}={rendered}\n")


def command_bootstrap(args: argparse.Namespace) -> int:
    if REGISTRY_PATH.exists() and not args.force:
        raise ValueError(f"registry already exists: {REGISTRY_PATH}")
    rows = rulesets.read_legacy_ruleset_rows(REMOTE_RULESETS_PATH)
    registry = rulesets.registry_from_legacy_rows(rows)
    fetched, errors = rulesets.fetch_registry_sources(registry)
    if errors:
        raise ValueError("upstream fetch failed: " + json.dumps(errors, ensure_ascii=False))

    changed = rulesets.sync_registry_sources(ROOT, registry, fetched)
    rulesets.validate_registry(registry)
    REGISTRY_PATH.write_text(
        rulesets.render_registry(registry), encoding="utf-8", newline="\n"
    )
    rulesets.rewrite_rule_manifests(ROOT, registry)
    license_text = rulesets.fetch_url(rulesets.UPSTREAM_LICENSE_URL)
    license_path = ROOT / rulesets.LICENSE_RELATIVE_PATH
    license_path.parent.mkdir(parents=True, exist_ok=True)
    license_path.write_text(license_text, encoding="utf-8", newline="\n")
    print(f"bootstrapped_sources={len(registry['sources'])}")
    print(f"written_snapshots={len(changed)}")
    return 0


def command_validate(_args: argparse.Namespace) -> int:
    registry = rulesets.load_registry(REGISTRY_PATH, ROOT)
    errors = [
        *rulesets.validate_snapshots(ROOT, registry),
        *rulesets.validate_rule_manifests(ROOT, registry),
    ]
    if errors:
        for error in errors:
            print(f"FAIL - {error}", file=sys.stderr)
        return 1
    print("ruleset_governance=PASS")
    print(f"sources={len(registry['sources'])}")
    print(f"rules={sum(entry['rule_count'] for entry in registry['sources'])}")
    return 0


def command_monitor(args: argparse.Namespace) -> int:
    registry = rulesets.load_registry(REGISTRY_PATH, ROOT)
    fetched, errors = rulesets.fetch_registry_sources(registry)
    simulated = args.simulate_source_id or ""
    if simulated:
        if simulated not in fetched:
            raise ValueError(f"cannot simulate unavailable source: {simulated}")
        # 模拟只改当前运行内存，不写仓库，也不能进入批准 PR。
        fetched[simulated] += "\nDOMAIN-SUFFIX,v5-monitor-simulation.invalid\n"
    report = rulesets.build_monitor_report(ROOT, registry, fetched, errors)
    report["simulated_source_id"] = simulated
    json_path = Path(args.json_out).resolve()
    markdown_path = Path(args.markdown_out).resolve()
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    markdown_path.write_text(
        rulesets.render_monitor_markdown(report, simulated),
        encoding="utf-8",
        newline="\n",
    )
    write_github_outputs(
        args.github_output,
        {
            "status": report["status"],
            "changed_count": report["changed_count"],
            "error_count": report["error_count"],
            "snapshot_drift_count": report["snapshot_drift_count"],
            "action_required": report["action_required"],
            "simulated": bool(simulated),
        },
    )
    print(f"monitor_status={report['status']}")
    print(f"changed_count={report['changed_count']}")
    print(f"error_count={report['error_count']}")
    print(f"snapshot_drift_count={report['snapshot_drift_count']}")
    return 0


def command_sync(args: argparse.Namespace) -> int:
    registry = rulesets.load_registry(REGISTRY_PATH, ROOT)
    fetched, errors = rulesets.fetch_registry_sources(registry)
    if errors:
        raise ValueError("upstream fetch failed: " + json.dumps(errors, ensure_ascii=False))
    changed = rulesets.sync_registry_sources(ROOT, registry, fetched)
    if changed:
        REGISTRY_PATH.write_text(
            rulesets.render_registry(registry), encoding="utf-8", newline="\n"
        )
        rulesets.rewrite_rule_manifests(ROOT, registry)
    write_github_outputs(
        args.github_output,
        {
            "changed_count": len(changed),
            "changed_ids": changed,
            "has_changes": bool(changed),
        },
    )
    print(f"changed_count={len(changed)}")
    print("changed_ids=" + ",".join(changed))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap = subparsers.add_parser("bootstrap", help="Create initial governed snapshots.")
    bootstrap.add_argument("--force", action="store_true")
    bootstrap.set_defaults(handler=command_bootstrap)

    validate = subparsers.add_parser("validate", help="Validate tracked snapshots and manifests.")
    validate.set_defaults(handler=command_validate)

    monitor = subparsers.add_parser("monitor", help="Compare current upstream semantics.")
    monitor.add_argument("--json-out", required=True)
    monitor.add_argument("--markdown-out", required=True)
    monitor.add_argument("--github-output", default=os.environ.get("GITHUB_OUTPUT"))
    monitor.add_argument("--simulate-source-id", default="")
    monitor.set_defaults(handler=command_monitor)

    sync = subparsers.add_parser("sync", help="Apply current upstream semantics to snapshots.")
    sync.add_argument("--github-output", default=os.environ.get("GITHUB_OUTPUT"))
    sync.set_defaults(handler=command_sync)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.handler(args)
    except Exception as exc:  # noqa: BLE001 - CLI must return one actionable error.
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
