#!/usr/bin/env python3
"""Apply manually approved S1.1 updates for GitHub PR automation."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AI_SEEDS = ROOT / "references" / "ai-proxy-domain-seeds.txt"
AI_CANDIDATES = ROOT / "references" / "ai-proxy-domain-candidates.txt"
DECISIONS = ROOT / "docs" / "rule-source-decisions.md"


COMMAND_PATTERNS = {
    "approve_all": re.compile(r"^/approve-s1\.1-update\s*$", re.IGNORECASE | re.MULTILINE),
    "approve_ai": re.compile(r"^/approve-ai-domain\s+([a-z0-9.-]+)\s*$", re.IGNORECASE | re.MULTILINE),
    "approve_source": re.compile(r"^/approve-source-update\s+([a-z0-9._-]+)\s*$", re.IGNORECASE | re.MULTILINE),
    "reject_ai": re.compile(r"^/reject-ai-domain\s+([a-z0-9.-]+)\s*$", re.IGNORECASE | re.MULTILINE),
    "reject_source": re.compile(r"^/reject-source-update\s+([a-z0-9._-]+)\s*$", re.IGNORECASE | re.MULTILINE),
}


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


def clean_domain(value: str) -> str:
    domain = value.strip().lower().lstrip("*.").strip(".")
    if not re.fullmatch(r"[a-z0-9.-]+\.[a-z0-9.-]+", domain):
        raise ValueError(f"invalid domain: {value}")
    return domain


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines() if path.exists() else []


def write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8", newline="\n")


def rule_line_for_domain(domain: str) -> str:
    return f"DOMAIN-SUFFIX,{domain}"


def approve_ai_domain(domain: str) -> None:
    rule = rule_line_for_domain(clean_domain(domain))
    seed_lines = read_lines(AI_SEEDS)
    if not any(line.strip().lower() == rule.lower() for line in seed_lines):
        if seed_lines and seed_lines[-1].strip():
            seed_lines.append("")
        seed_lines.append("# Manually approved from GitHub Issue command.")
        seed_lines.append(rule)
        write_lines(AI_SEEDS, seed_lines)

    candidate_lines = read_lines(AI_CANDIDATES)
    filtered = [
        line for line in candidate_lines
        if clean_compare_rule(line) != rule.lower()
    ]
    if filtered != candidate_lines:
        write_lines(AI_CANDIDATES, filtered)


def clean_compare_rule(line: str) -> str:
    cleaned = line.split("#", 1)[0].strip().lower()
    if not cleaned:
        return ""
    parts = [part.strip() for part in cleaned.split(",") if part.strip()]
    if len(parts) >= 2 and parts[0] in {"domain", "domain-suffix"}:
        return f"domain-suffix,{parts[1].lstrip('*.').strip('.')}"
    return cleaned


def append_decision(message: str, issue_number: str, author: str) -> None:
    lines = read_lines(DECISIONS)
    if not lines:
        lines = [
            "# S1.1 Rule Source Decisions",
            "",
            "Manual approval/rejection decisions from GitHub Issue comments.",
            "",
        ]
    lines.append(f"- Issue #{issue_number}, {author}: {message}")
    write_lines(DECISIONS, lines)


def rebuild_and_check() -> None:
    run([sys.executable, "scripts/build-s1-1-stabilized.py"])
    run([sys.executable, "scripts/sync-rule-source-registry.py"])
    run([sys.executable, "scripts/check-s1-1-static.py"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply approved S1.1 update commands.")
    parser.add_argument("--comment", default=os.environ.get("COMMENT_BODY", ""))
    parser.add_argument("--issue-number", default=os.environ.get("ISSUE_NUMBER", "unknown"))
    parser.add_argument("--author", default=os.environ.get("COMMENT_AUTHOR", "unknown"))
    args = parser.parse_args()

    comment = args.comment.strip()
    if not comment:
        print("no comment body supplied", file=sys.stderr)
        return 2

    applied = False

    if COMMAND_PATTERNS["approve_all"].search(comment):
        run([sys.executable, "scripts/sync-rule-source-registry.py", "--source-id", "ALL"])
        rebuild_and_check()
        append_decision("approved all current S1.1 source baselines", args.issue_number, args.author)
        applied = True

    for match in COMMAND_PATTERNS["approve_source"].finditer(comment):
        source_id = match.group(1)
        run([sys.executable, "scripts/sync-rule-source-registry.py", "--source-id", source_id])
        rebuild_and_check()
        append_decision(f"approved source update `{source_id}`", args.issue_number, args.author)
        applied = True

    for match in COMMAND_PATTERNS["approve_ai"].finditer(comment):
        domain = clean_domain(match.group(1))
        approve_ai_domain(domain)
        rebuild_and_check()
        append_decision(f"approved AI domain `{domain}`", args.issue_number, args.author)
        applied = True

    for match in COMMAND_PATTERNS["reject_source"].finditer(comment):
        source_id = match.group(1)
        append_decision(f"rejected source update `{source_id}`", args.issue_number, args.author)
        applied = True

    for match in COMMAND_PATTERNS["reject_ai"].finditer(comment):
        domain = clean_domain(match.group(1))
        append_decision(f"rejected AI domain `{domain}`", args.issue_number, args.author)
        applied = True

    if not applied:
        print("no recognized S1.1 approval command")
        return 0

    print("approved_update_applied=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
