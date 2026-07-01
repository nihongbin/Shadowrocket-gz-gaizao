#!/usr/bin/env python3
"""Build S0 Shadowrocket scenario config from Johnshall whitelist rules.

S0 is not a pure DNS privacy fix. It is a China-local experience plus US proxy
fallback scenario. Johnshall rules are used as the [Rule] body, while [Host]
is generated only from the China-local domain pool.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = (
    "https://raw.githubusercontent.com/Johnshall/"
    "Shadowrocket-ADBlock-Rules-Forever/release/sr_top500_whitelist.conf"
)
DEFAULT_SEEDS_PATH = ROOT / "references" / "china-local-domain-seeds.txt"
DEFAULT_OUTPUT_PATH = ROOT / "configs" / "S0-scenario-cn-us-account-aggressive-v0.conf"

ALLOWED_RULE_TYPES = {
    "DOMAIN",
    "DOMAIN-SUFFIX",
    "DOMAIN-KEYWORD",
    "IP-CIDR",
    "IP-CIDR6",
    "GEOIP",
    "FINAL",
}

# 海外账号侧先于 Johnshall 白名单强制走代理，避免被上游 DIRECT 规则误放行。
ACCOUNT_PROXY_DOMAINS = [
    "tiktok.com",
    "tiktokv.com",
    "tiktokcdn.com",
    "tiktokcdn-us.com",
    "byteoversea.com",
    "musical.ly",
    "muscdn.com",
    "ibyteimg.com",
    "ibytedtos.com",
    "ttwstatic.com",
    "instagram.com",
    "cdninstagram.com",
    "facebook.com",
    "fbcdn.net",
    "meta.com",
    "threads.net",
    "youtube.com",
    "youtu.be",
    "googlevideo.com",
    "ytimg.com",
    "google.com",
    "gstatic.com",
    "googleapis.com",
    "x.com",
    "twitter.com",
    "twimg.com",
    "t.co",
    "openai.com",
    "chatgpt.com",
    "anthropic.com",
    "claude.ai",
]

TENCENT_HINTS = ("tencent", "qq", "wechat", "weixin", "qcloud", "myqcloud")
ALI_HINTS = (
    "alibaba",
    "alipay",
    "taobao",
    "tmall",
    "alicdn",
    "aliyun",
    "alimama",
    "mmstat",
)


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "s0-johnshall-builder/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8-sig")


def read_source(url: str, source_file: Path | None) -> str:
    if source_file:
        return source_file.read_text(encoding="utf-8-sig")
    return fetch_text(url)


def extract_rule_section(text: str) -> list[str]:
    lines: list[str] = []
    in_rule = False
    for raw in text.splitlines():
        line = raw.strip()
        if line == "[Rule]":
            in_rule = True
            continue
        if in_rule and line.startswith("[") and line.endswith("]"):
            break
        if in_rule:
            lines.append(line)
    return lines


def strip_inline_comment(line: str) -> str:
    if not line or line.startswith("#"):
        return ""
    return line.split("#", 1)[0].strip()


def parse_rule(line: str) -> tuple[str | None, dict[str, str | None]]:
    cleaned = strip_inline_comment(line)
    if not cleaned:
        return None, {"reason": None}

    parts = [part.strip() for part in cleaned.split(",") if part.strip()]
    if not parts:
        return None, {"reason": None}

    rule_type = parts[0].upper()
    if rule_type not in ALLOWED_RULE_TYPES:
        return None, {"reason": f"unsupported:{rule_type}"}

    if rule_type == "FINAL":
        return "FINAL,PROXY", {"reason": None}

    if len(parts) < 3:
        return None, {"reason": f"malformed:{rule_type}"}

    policy = parts[2].upper()
    if policy not in {"DIRECT", "PROXY"}:
        return None, {"reason": f"unsupported-policy:{policy}"}

    parts[0] = rule_type
    parts[2] = policy

    # IP 规则不应该反向引入 DNS 变量；没有 no-resolve 时自动补上。
    if rule_type in {"IP-CIDR", "IP-CIDR6"} and not any(
        item.lower() == "no-resolve" for item in parts[3:]
    ):
        parts.append("no-resolve")

    return ",".join(parts), {"reason": None}


def is_domain_sensitive(domain: str) -> bool:
    normalized = domain.lower().lstrip("*.").strip(".")
    return any(
        normalized == item or normalized.endswith("." + item)
        for item in ACCOUNT_PROXY_DOMAINS
    )


def read_seed_domains(seeds_path: Path) -> set[str]:
    domains: set[str] = set()
    for raw in seeds_path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip().lower().lstrip("*.").strip(".")
        if not line or " " in line or "/" in line or "." not in line:
            continue
        if is_domain_sensitive(line):
            continue
        domains.add(line)
    return domains


def rule_parts(rule: str) -> list[str]:
    return [part.strip() for part in rule.split(",") if part.strip()]


def is_direct_domain_rule(rule: str) -> bool:
    parts = rule_parts(rule)
    return (
        len(parts) >= 3
        and parts[0] in {"DOMAIN", "DOMAIN-SUFFIX"}
        and parts[2] == "DIRECT"
    )


def collect_host_entries(rules: list[str], seed_domains: set[str]) -> list[tuple[str, bool]]:
    entries: dict[str, bool] = {}

    # 人工种子表是中国本地体验的主入口，统一生成 root + wildcard。
    for domain in sorted(seed_domains):
        entries[domain] = True

    # 只自动吸收 Johnshall 中明确的 .cn DIRECT 域名，不把全部 DIRECT 当中国白名单。
    for rule in rules:
        if not is_direct_domain_rule(rule):
            continue
        parts = rule_parts(rule)
        rule_type, domain = parts[0], parts[1].lower().strip(".")
        if not domain.endswith(".cn") or "." not in domain or is_domain_sensitive(domain):
            continue
        entries[domain] = rule_type == "DOMAIN-SUFFIX"

    return sorted(entries.items())


def dns_server_for_domain(domain: str) -> str:
    lowered = domain.lower()
    if any(hint in lowered for hint in TENCENT_HINTS):
        return "119.29.29.29"
    if any(hint in lowered for hint in ALI_HINTS):
        return "223.5.5.5"
    return "223.5.5.5"


def build_host_lines(entries: list[tuple[str, bool]]) -> list[str]:
    host_lines = ["localhost = 127.0.0.1"]
    seen = set(host_lines)

    def add(line: str) -> None:
        if line not in seen:
            seen.add(line)
            host_lines.append(line)

    for domain, wildcard in entries:
        server = dns_server_for_domain(domain)
        add(f"{domain} = server:{server}")
        if wildcard:
            add(f"*.{domain} = server:{server}")

    return host_lines


def build_china_direct_rules(entries: list[tuple[str, bool]]) -> list[str]:
    rules: list[str] = []
    seen: set[str] = set()

    def add(rule: str) -> None:
        if rule not in seen:
            seen.add(rule)
            rules.append(rule)

    for domain, wildcard in entries:
        if is_domain_sensitive(domain):
            continue
        if wildcard:
            add(f"DOMAIN-SUFFIX,{domain},DIRECT")
        else:
            add(f"DOMAIN,{domain},DIRECT")

    return rules


def normalise_upstream_rules(raw_rule_lines: list[str]) -> tuple[list[str], dict[str, int]]:
    rules: list[str] = []
    dropped: dict[str, int] = {}

    for raw in raw_rule_lines:
        rule, meta = parse_rule(raw)
        reason = meta.get("reason")
        if reason:
            dropped[reason] = dropped.get(reason, 0) + 1
            continue
        if not rule or rule.startswith("FINAL,"):
            continue
        rules.append(rule)

    return rules, dropped


def format_dropped(dropped: dict[str, int]) -> str:
    if not dropped:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in sorted(dropped.items()))


def build_config(source_text: str, seeds_path: Path, source_url: str) -> str:
    source_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    raw_rule_lines = extract_rule_section(source_text)
    upstream_rules, dropped = normalise_upstream_rules(raw_rule_lines)
    seed_domains = read_seed_domains(seeds_path)
    host_entries = collect_host_entries(upstream_rules, seed_domains)
    host_lines = build_host_lines(host_entries)
    china_direct_rules = build_china_direct_rules(host_entries)
    account_rules = [f"DOMAIN-SUFFIX,{domain},PROXY" for domain in ACCOUNT_PROXY_DOMAINS]

    lines = [
        "# S0 scenario: China local experience + US proxy fallback",
        f"# Upstream URL: {source_url}",
        f"# Upstream SHA256: {source_hash}",
        "# License: Johnshall upstream uses CC BY-SA 4.0; keep attribution when sharing.",
        "# Metadata is stable: no current runtime timestamp is embedded.",
        f"# Rule stats: account_proxy={len(account_rules)}, china_direct={len(china_direct_rules)}, upstream_kept={len(upstream_rules)}, host={len(host_lines)}, dropped={format_dropped(dropped)}",
        "",
        "[General]",
        "bypass-system = true",
        "skip-proxy = 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, localhost, *.local, captive.apple.com",
        "tun-excluded-routes = 10.0.0.0/8, 17.0.0.0/8, 100.64.0.0/10, 127.0.0.0/8, 169.254.0.0/16, 172.16.0.0/12, 192.168.0.0/16, 224.0.0.0/4, 240.0.0.0/4",
        "dns-server = https://cloudflare-dns.com/dns-query, https://dns.google/dns-query",
        "fallback-dns-server = https://cloudflare-dns.com/dns-query, https://dns.google/dns-query",
        "ipv6 = false",
        "prefer-ipv6 = false",
        "dns-fallback-system = false",
        "dns-direct-system = false",
        "dns-direct-fallback-proxy = true",
        "hijack-dns = 8.8.8.8:53, 8.8.4.4:53, 1.1.1.1:53, 1.0.0.1:53",
        "private-ip-answer = true",
        "udp-policy-not-supported-behaviour = REJECT",
        "use-local-host-item-for-proxy = false",
        "",
        "[Host]",
        "# Only China-local domains from references/china-local-domain-seeds.txt and explicit .cn DIRECT rules.",
        *host_lines,
        "",
        "[Rule]",
        "# Account-side guard: keep overseas accounts on PROXY before Johnshall rules.",
        *account_rules,
        "",
        "# China-local guard: keep known China app domains on DIRECT before Johnshall fallback.",
        *china_direct_rules,
        "",
        "# Johnshall sr_top500_whitelist.conf rule body.",
        *upstream_rules,
        "FINAL,PROXY",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build S0 Shadowrocket config.")
    parser.add_argument("--source-url", default=SOURCE_URL)
    parser.add_argument("--source-file", type=Path, help="Use a local fixture instead of the remote upstream.")
    parser.add_argument("--seeds-file", type=Path, default=DEFAULT_SEEDS_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--check", action="store_true", help="Check that output is already up to date.")
    args = parser.parse_args()

    source_text = read_source(args.source_url, args.source_file)
    output = build_config(source_text, args.seeds_file, args.source_url)

    if args.check:
        if not args.output.exists():
            print(f"missing: {args.output}", file=sys.stderr)
            return 1
        if args.output.read_text(encoding="utf-8") != output:
            print(f"stale: {args.output}", file=sys.stderr)
            return 1
        print(f"up to date: {args.output}")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8", newline="\n")
    print(f"wrote: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
