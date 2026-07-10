#!/usr/bin/env python3
"""Verify that the only private V5 and public S5 keep identical routing logic."""

from __future__ import annotations

import hashlib
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import v5_rulesets as governed_rulesets


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = ROOT / "local" / "private-configs"
PRIVATE_V5 = PRIVATE_ROOT / "S1-default-lazy-proxy-doh-1-stable-enhanced-cnapp-v5.conf"
PUBLIC_S5 = ROOT / "configs" / "S5-scenario-cn-us-v5-mvp-v0.conf"
RULESET_REGISTRY = ROOT / governed_rulesets.REGISTRY_RELATIVE_PATH
EXPECTED_PRIVATE_SHA256 = "D0478F6D913942FCF80DDC2D87650F98B50D7AC7E2D0AF49766C22804988F9DD"
PUBLIC_SECTIONS = ("General", "Rule", "Host")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def effective_sections(text: str) -> "OrderedDict[str, list[str]]":
    sections: "OrderedDict[str, list[str]]" = OrderedDict()
    current: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip()
            sections.setdefault(current, [])
            continue
        if current and line and not line.startswith("#"):
            sections[current].append(line)
    return sections


def ruleset_identity_map() -> dict[str, str]:
    registry = governed_rulesets.load_registry(RULESET_REGISTRY, ROOT)
    identities: dict[str, str] = {}
    for entry in registry["sources"]:
        identity = f"v5-governed:{entry['id']}"
        identities[entry["upstream_url"]] = identity
        identities[entry["public_url"]] = identity
    return identities


def normalize_rule_identities(lines: list[str]) -> list[str]:
    identities = ruleset_identity_map()
    normalized: list[str] = []
    for line in lines:
        parts = [part.strip() for part in line.split(",", 2)]
        if len(parts) == 3 and parts[0].upper() == "RULE-SET":
            identity = identities.get(parts[1])
            if identity:
                normalized.append(f"RULE-SET,{identity},{parts[2]}")
                continue
        normalized.append(line)
    return normalized


def compare_effective_sections(private_text: str, public_text: str) -> dict[str, bool]:
    private = effective_sections(private_text)
    public = effective_sections(public_text)
    result = {name: private.get(name) == public.get(name) for name in PUBLIC_SECTIONS}
    result["Rule"] = normalize_rule_identities(private.get("Rule", [])) == normalize_rule_identities(
        public.get("Rule", [])
    )
    return result


def main() -> int:
    errors: list[str] = []
    if not PRIVATE_V5.exists():
        errors.append(f"private V5 is missing: {PRIVATE_V5}")
    if not PUBLIC_S5.exists():
        errors.append(f"public S5 is missing: {PUBLIC_S5}")
    if errors:
        for error in errors:
            print(f"FAIL - {error}", file=sys.stderr)
        return 1

    private_hash = sha256_file(PRIVATE_V5)
    if private_hash != EXPECTED_PRIVATE_SHA256:
        errors.append(
            f"private V5 hash mismatch: expected {EXPECTED_PRIVATE_SHA256}, got {private_hash}"
        )

    # 私有目录只允许保留当前实测基盘，避免手机再次导入旧测试版本。
    private_configs = sorted(PRIVATE_ROOT.rglob("*.conf"))
    if private_configs != [PRIVATE_V5]:
        errors.append(
            "local/private-configs must contain only the verified V5 baseline"
        )

    public_configs = sorted((ROOT / "configs").glob("*.conf"))
    if public_configs != [PUBLIC_S5]:
        errors.append("configs must contain only the governed public S5 template")

    comparison = compare_effective_sections(
        PRIVATE_V5.read_text(encoding="utf-8-sig"),
        PUBLIC_S5.read_text(encoding="utf-8-sig"),
    )
    for section, matches in comparison.items():
        if not matches:
            errors.append(f"effective [{section}] differs between private V5 and public S5")

    ignored = subprocess.run(
        ["git", "check-ignore", "-q", str(PRIVATE_V5.relative_to(ROOT))],
        cwd=ROOT,
        check=False,
    )
    if ignored.returncode != 0:
        errors.append("private V5 is not covered by .gitignore")

    if errors:
        for error in errors:
            print(f"FAIL - {error}", file=sys.stderr)
        return 1

    public = effective_sections(PUBLIC_S5.read_text(encoding="utf-8-sig"))
    print("consistency=PASS")
    print(f"private_sha256={private_hash}")
    print(f"public_sha256={sha256_file(PUBLIC_S5)}")
    for section in PUBLIC_SECTIONS:
        print(f"{section.lower()}_effective={len(public[section])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
