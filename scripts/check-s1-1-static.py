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

FORBIDDEN_HIJACK_DNS = ("114.114.114.114", "223.5.5.5", "223.6.6.6", "119.29.29.29")

REQUIRED_CHINA_LOGFIX_DOMAINS = (
    "bytemaimg.com",
    "bytescm.com",
    "byteeffecttos.com",
    "bytemastatic.com",
    "pangolin-sdk-toutiao1.com",
    "qznovelvod.com",
    "qishui.com",
    "yunxindns.com",
    "yunxinfw.com",
    "fqnovelpic.com",
    "dailygn.com",
    "miaozhen.com",
    "snssdk.insta360.com",
)

REQUIRED_OVERSEAS_PROXY_RULES = (
    "DOMAIN-SUFFIX,crunchyroll.com,PROXY",
    "DOMAIN-SUFFIX,snapkit.com,PROXY",
    "DOMAIN-SUFFIX,revenuecat.com,PROXY",
    "DOMAIN-SUFFIX,bugsnag.com,PROXY",
    "DOMAIN-SUFFIX,branch.io,PROXY",
    "DOMAIN-SUFFIX,singular.net,PROXY",
    "DOMAIN-SUFFIX,sprig.com,PROXY",
    "DOMAIN-SUFFIX,instabug.com,PROXY",
    "DOMAIN-SUFFIX,gorgias.chat,PROXY",
    "DOMAIN-SUFFIX,gorgias.help,PROXY",
    "DOMAIN-SUFFIX,ip.net.coffee,PROXY",
    "DOMAIN-SUFFIX,ipapi.co,PROXY",
    "DOMAIN-SUFFIX,appsflyersdk.com,PROXY",
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


def first_index(text: str, needle: str) -> int:
    index = text.find(needle)
    return index if index >= 0 else sys.maxsize


def config_lines(text: str) -> set[str]:
    return {line.strip() for line in text.splitlines() if line.strip()}


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

    hijack_line = next((line.strip() for line in text.splitlines() if line.strip().lower().startswith("hijack-dns =")), "")
    if not hijack_line:
        fail("S1.1 missing hijack-dns line", failures)
    else:
        forbidden_dns = [dns for dns in FORBIDDEN_HIJACK_DNS if dns in hijack_line]
        if forbidden_dns:
            fail("hijack-dns contains China DNS: " + ", ".join(forbidden_dns), failures)
        else:
            ok("hijack-dns excludes China DNS servers")

    lines = config_lines(text)
    for domain in REQUIRED_CHINA_LOGFIX_DOMAINS:
        host_present = any(
            line.startswith(f"{domain} = server:") or line.startswith(f"*.{domain} = server:")
            for line in lines
        )
        direct_rule = f"DOMAIN-SUFFIX,{domain},DIRECT"
        if host_present and direct_rule in lines:
            ok(f"S1.1 includes Host + DIRECT for China logfix domain {domain}")
        else:
            fail(f"S1.1 missing Host or DIRECT for China logfix domain {domain}", failures)

    if "DOMAIN-SUFFIX,insta360.com,DIRECT" in lines:
        fail("S1.1 must not DIRECT the whole insta360.com domain", failures)
    else:
        ok("S1.1 does not DIRECT the whole insta360.com domain")

    if any(line in lines for line in ("insta360.com = server:223.5.5.5", "*.insta360.com = server:223.5.5.5")):
        fail("S1.1 must not create Host entries for the whole insta360.com domain", failures)
    else:
        ok("S1.1 does not create Host entries for the whole insta360.com domain")

    china_guard_index = first_index(text, "# China-local guard:")
    for rule in REQUIRED_OVERSEAS_PROXY_RULES:
        rule_index = first_index(text, rule)
        if rule_index < china_guard_index:
            ok(f"S1.1 overseas proxy rule appears before China DIRECT: {rule}")
        else:
            fail(f"S1.1 missing overseas proxy rule before China DIRECT: {rule}", failures)

    browserleaks_index = first_index(text, "DOMAIN-SUFFIX,browserleaks.com,PROXY")
    if browserleaks_index < china_guard_index:
        ok("browserleaks.com remains PROXY before China DIRECT")
    else:
        fail("browserleaks.com is missing or appears after China DIRECT", failures)

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
