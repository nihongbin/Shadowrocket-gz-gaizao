#!/usr/bin/env python3
"""Static checks for S1.1 public template and local-private boundaries."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "S1-1-scenario-cn-us-lazy-stabilized-v0.conf"
REGISTRY = ROOT / "references" / "rule-source-registry.json"
PUBLIC_DIRS = [ROOT / "configs", ROOT / "docs", ROOT / "references"]
URL_PATTERN = re.compile(r"https?://[^\s,]+")

NODE_PATTERNS = ("ss://", "ssr://", "vmess://", "vless://", "trojan://", "hysteria://")
SECRET_PATTERNS = (
    re.compile(r"token\s*=", re.IGNORECASE),
    re.compile(r"password\s*=", re.IGNORECASE),
    re.compile(r"secret\s*=", re.IGNORECASE),
    re.compile(r"subscribe", re.IGNORECASE),
)


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)
    print(f"FAIL - {message}")


def ok(message: str) -> None:
    print(f"PASS - {message}")


def section_names(text: str) -> set[str]:
    names: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            names.add(stripped[1:-1].strip())
    return names


def extract_urls(text: str) -> set[str]:
    return {match.rstrip(").,") for match in URL_PATTERN.findall(text)}


def registry_urls() -> set[str]:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return {str(item["url"]) for item in data.get("sources", [])}


def local_private_ignored() -> bool:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8") if (ROOT / ".gitignore").exists() else ""
    lines = {line.strip() for line in gitignore.splitlines() if line.strip() and not line.strip().startswith("#")}
    return "/local/" in lines or "local/" in lines or "/local/private-configs/" in lines


def public_private_config_hits() -> list[Path]:
    hits: list[Path] = []
    for base in PUBLIC_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except UnicodeDecodeError:
                continue
            if path.suffix.lower() == ".conf" and "# PRIVATE SCENARIO MERGED CONFIG" in text:
                hits.append(path)
    return hits


def main() -> int:
    failures: list[str] = []
    if not CONFIG.exists():
        fail(f"missing S1.1 config: {CONFIG}", failures)
        return 1

    text = CONFIG.read_text(encoding="utf-8")
    sections = section_names(text)
    for name in ("General", "Host", "Rule"):
        if name in sections:
            ok(f"S1.1 contains [{name}]")
        else:
            fail(f"S1.1 missing [{name}]", failures)

    for pattern in NODE_PATTERNS:
        if pattern in text:
            fail(f"S1.1 contains node URI pattern {pattern}", failures)
    if not any(pattern in text for pattern in NODE_PATTERNS):
        ok("S1.1 has no node URI protocol lines")

    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            fail(f"S1.1 contains suspicious secret/subscription pattern: {pattern.pattern}", failures)
    if not any(pattern.search(text) for pattern in SECRET_PATTERNS):
        ok("S1.1 has no obvious token/password/secret/subscribe patterns")

    forbidden_literals = [
        "[MITM]",
        "[URL Rewrite]",
        "server:system",
        "dns-server = system",
        "fallback-dns-server = system",
        "RULE-SET,https://raw.githubusercontent.com/iab0x00/ProxyRules/main/Rule/AI.txt",
        "rule/QuantumultX/",
    ]
    for literal in forbidden_literals:
        if literal in text:
            fail(f"S1.1 contains forbidden literal: {literal}", failures)
        else:
            ok(f"S1.1 does not contain {literal}")

    final_line = next((line.strip() for line in reversed(text.splitlines()) if line.strip()), "")
    if final_line == "FINAL,PROXY":
        ok("S1.1 final non-empty line is FINAL,PROXY")
    else:
        fail(f"S1.1 final non-empty line is {final_line!r}", failures)

    if "https://cloudflare-dns.com/dns-query#proxy" in text and "https://dns.google/dns-query#proxy" in text:
        ok("S1.1 contains proxy DoH and second-provider fallback")
    else:
        fail("S1.1 missing proxy DoH or second-provider fallback", failures)

    if local_private_ignored():
        ok("local/private-configs is covered by .gitignore local rule")
    else:
        fail("local/private-configs is not ignored by .gitignore", failures)

    hits = public_private_config_hits()
    if hits:
        fail("private merged config marker found in public dirs: " + ", ".join(str(path.relative_to(ROOT)) for path in hits), failures)
    else:
        ok("no private merged config marker found in configs/docs/references")

    if not REGISTRY.exists():
        fail(f"missing rule source registry: {REGISTRY}", failures)
    else:
        config_urls = extract_urls(text)
        registered = registry_urls()
        missing = sorted(config_urls - registered)
        if missing:
            fail("registry missing S1.1 URLs: " + ", ".join(missing), failures)
        else:
            ok("rule-source registry covers all S1.1 remote URLs")

    if failures:
        print(f"static_check=FAIL failures={len(failures)}")
        return 1
    print("static_check=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
