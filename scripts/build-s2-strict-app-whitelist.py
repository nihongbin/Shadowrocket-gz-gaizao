#!/usr/bin/env python3
"""Build S2 strict China-app whitelist config from Johnshall lazy.conf.

S2 is stricter than S1: only China-local domains from this project's seed file
may go DIRECT. lazy.conf is used only as a source of mature PROXY rules.
Unknown domains and any unapproved DIRECT rules fall through to FINAL,PROXY.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = "https://johnshall.github.io/Shadowrocket-ADBlock-Rules-Forever/lazy.conf"
DEFAULT_SEEDS_PATH = ROOT / "references" / "china-local-domain-seeds.txt"
DEFAULT_OUTPUT_PATH = ROOT / "configs" / "S2-scenario-cn-us-strict-app-whitelist-v0.conf"

ALLOWED_RULE_TYPES = {
    "RULE-SET",
    "DOMAIN",
    "DOMAIN-SUFFIX",
    "DOMAIN-KEYWORD",
    "DOMAIN-WILDCARD",
    "DOMAIN-SET",
    "IP-CIDR",
    "IP-CIDR6",
    "IP-ASN",
    "GEOIP",
    "FINAL",
}

# 这些域名既可能服务中国业务，也可能服务海外业务；S2 先不允许它们直连。
AMBIGUOUS_CHINA_DOMAINS = {
    "bytedance.com",
    "byteimg.com",
    "snssdk.com",
}

LAN_DIRECT_RULES = [
    "DOMAIN,localhost,DIRECT",
    "DOMAIN-SUFFIX,local,DIRECT",
    "IP-CIDR,10.0.0.0/8,DIRECT,no-resolve",
    "IP-CIDR,100.64.0.0/10,DIRECT,no-resolve",
    "IP-CIDR,127.0.0.0/8,DIRECT,no-resolve",
    "IP-CIDR,169.254.0.0/16,DIRECT,no-resolve",
    "IP-CIDR,172.16.0.0/12,DIRECT,no-resolve",
    "IP-CIDR,192.168.0.0/16,DIRECT,no-resolve",
]

# DNS/IP 测试站本身必须先走代理，否则测试页会直接看到真实出口。
TEST_PROXY_DOMAINS = [
    "browserleaks.com",
    "browserleaks.org",
    "dnsleaktest.com",
    "ipleak.net",
    "ippure.com",
    "ipinfo.io",
    "ip.sb",
    "whatismyip.com",
    "whatismyipaddress.com",
    "ifconfig.me",
    "icanhazip.com",
    "ipify.org",
    "ident.me",
    "myip.com",
]

# 海外账号、AI、流媒体核心域名先于中国白名单强制走代理。
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
    "netflix.com",
    "nflxvideo.net",
    "nflximg.net",
    "nflxso.net",
    "disneyplus.com",
    "disney-plus.net",
    "hulu.com",
    "max.com",
    "hbomax.com",
    "spotify.com",
    "scdn.co",
    "telegram.org",
    "t.me",
    "paypal.com",
    "paypalobjects.com",
    "google.com",
    "gstatic.com",
    "googleapis.com",
    "googleusercontent.com",
    "github.com",
    "githubusercontent.com",
    "x.com",
    "twitter.com",
    "twimg.com",
    "t.co",
    "openai.com",
    "chatgpt.com",
    "oaistatic.com",
    "oaiusercontent.com",
    "anthropic.com",
    "claude.ai",
    "perplexity.ai",
    "gemini.google.com",
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
    req = urllib.request.Request(url, headers={"User-Agent": "s2-strict-builder/1.0"})
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


def split_rule(line: str) -> list[str]:
    return [part.strip() for part in line.split(",") if part.strip()]


def parse_proxy_rule(line: str) -> tuple[str | None, str | None]:
    cleaned = strip_inline_comment(line)
    if not cleaned:
        return None, None

    parts = split_rule(cleaned)
    if not parts:
        return None, None

    rule_type = parts[0].upper()
    if rule_type not in ALLOWED_RULE_TYPES:
        return None, f"unsupported:{rule_type}"

    if rule_type == "FINAL":
        return None, "dropped-final"

    if len(parts) < 3:
        return None, f"malformed:{rule_type}"

    policy = parts[2].upper()
    if policy == "DIRECT":
        if rule_type == "GEOIP" and len(parts) >= 2 and parts[1].upper() == "CN":
            return None, "dropped-geoip-cn-direct"
        return None, "dropped-direct"
    if policy != "PROXY":
        return None, f"unsupported-policy:{policy}"

    parts[0] = rule_type
    parts[2] = policy

    # IP 类代理规则加 no-resolve，避免域名匹配 IP 规则时额外触发本地 DNS。
    if rule_type in {"IP-CIDR", "IP-CIDR6"} and not any(
        item.lower() == "no-resolve" for item in parts[3:]
    ):
        parts.append("no-resolve")

    return ",".join(parts), None


def is_domain_sensitive(domain: str) -> bool:
    normalized = domain.lower().lstrip("*.").strip(".")
    return any(
        normalized == item or normalized.endswith("." + item)
        for item in ACCOUNT_PROXY_DOMAINS
    )


def is_ambiguous_china_domain(domain: str) -> bool:
    normalized = domain.lower().lstrip("*.").strip(".")
    return any(
        normalized == item or normalized.endswith("." + item)
        for item in AMBIGUOUS_CHINA_DOMAINS
    )


def read_seed_domains(seeds_path: Path) -> list[str]:
    domains: set[str] = set()
    for raw in seeds_path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip().lower().lstrip("*.").strip(".")
        if not line or " " in line or "/" in line or "." not in line:
            continue
        if is_domain_sensitive(line) or is_ambiguous_china_domain(line):
            continue
        domains.add(line)
    return sorted(domains)


def dns_server_for_domain(domain: str) -> str:
    lowered = domain.lower()
    if any(hint in lowered for hint in TENCENT_HINTS):
        return "119.29.29.29"
    if any(hint in lowered for hint in ALI_HINTS):
        return "223.5.5.5"
    return "223.5.5.5"


def build_host_lines(seed_domains: list[str]) -> list[str]:
    host_lines = ["localhost = 127.0.0.1"]
    seen = set(host_lines)

    def add(line: str) -> None:
        if line not in seen:
            seen.add(line)
            host_lines.append(line)

    for domain in seed_domains:
        server = dns_server_for_domain(domain)
        add(f"{domain} = server:{server}")
        add(f"*.{domain} = server:{server}")

    return host_lines


def build_china_direct_rules(seed_domains: list[str]) -> list[str]:
    rules: list[str] = []
    seen: set[str] = set()

    def add(rule: str) -> None:
        if rule not in seen:
            seen.add(rule)
            rules.append(rule)

    for domain in seed_domains:
        if is_domain_sensitive(domain) or is_ambiguous_china_domain(domain):
            continue
        add(f"DOMAIN-SUFFIX,{domain},DIRECT")

    return rules


def normalise_lazy_proxy_rules(raw_rule_lines: list[str]) -> tuple[list[str], dict[str, int]]:
    rules: list[str] = []
    dropped: dict[str, int] = {}

    for raw in raw_rule_lines:
        rule, reason = parse_proxy_rule(raw)
        if reason:
            dropped[reason] = dropped.get(reason, 0) + 1
            continue
        if not rule:
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
    lazy_proxy_rules, dropped = normalise_lazy_proxy_rules(raw_rule_lines)
    seed_domains = read_seed_domains(seeds_path)
    host_lines = build_host_lines(seed_domains)
    china_direct_rules = build_china_direct_rules(seed_domains)
    test_rules = [f"DOMAIN-SUFFIX,{domain},PROXY" for domain in TEST_PROXY_DOMAINS]
    account_rules = [f"DOMAIN-SUFFIX,{domain},PROXY" for domain in ACCOUNT_PROXY_DOMAINS]

    lines = [
        "# S2 scenario: strict China app whitelist + US proxy fallback",
        f"# Upstream URL: {source_url}",
        f"# Upstream SHA256: {source_hash}",
        "# License: Johnshall upstream uses CC BY-SA 4.0; keep attribution when sharing.",
        "# Metadata is stable: no current runtime timestamp is embedded.",
        f"# Rule stats: lan_direct={len(LAN_DIRECT_RULES)}, test_proxy={len(test_rules)}, account_proxy={len(account_rules)}, china_direct={len(china_direct_rules)}, lazy_proxy_kept={len(lazy_proxy_rules)}, host={len(host_lines)}, dropped={format_dropped(dropped)}",
        "",
        "[General]",
        "bypass-system = true",
        "skip-proxy = 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, localhost, *.local, captive.apple.com",
        "tun-excluded-routes = 10.0.0.0/8, 100.64.0.0/10, 127.0.0.0/8, 169.254.0.0/16, 172.16.0.0/12, 192.168.0.0/16, 224.0.0.0/4, 240.0.0.0/4",
        "ipv6 = false",
        "prefer-ipv6 = false",
        "dns-server = https://cloudflare-dns.com/dns-query#proxy, https://security.cloudflare-dns.com/dns-query#proxy",
        "fallback-dns-server = https://cloudflare-dns.com/dns-query#proxy, https://security.cloudflare-dns.com/dns-query#proxy",
        "dns-direct-system = false",
        "dns-fallback-system = false",
        "dns-direct-fallback-proxy = true",
        "hijack-dns = 8.8.8.8:53, 8.8.4.4:53",
        "private-ip-answer = true",
        "udp-policy-not-supported-behaviour = REJECT",
        "use-local-host-item-for-proxy = false",
        "block-quic = all-proxy",
        "",
        "[Host]",
        "# Only China-local domains from references/china-local-domain-seeds.txt.",
        "# Ambiguous cross-border domains are intentionally excluded in S2.",
        *host_lines,
        "",
        "[Rule]",
        "# LAN/private guard: allow local network access without proxy.",
        *LAN_DIRECT_RULES,
        "",
        "# DNS/IP test-site guard: keep leak-test pages on PROXY before any DIRECT app whitelist.",
        *test_rules,
        "",
        "# Account/AI/media guard: keep overseas apps on PROXY before China app whitelist.",
        *account_rules,
        "",
        "# China app whitelist: only explicitly approved China-local app domains may go DIRECT.",
        *china_direct_rules,
        "",
        "# Johnshall lazy.conf PROXY rules only. All lazy DIRECT/GEOIP/FINAL rules are dropped.",
        *lazy_proxy_rules,
        "FINAL,PROXY",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build S2 strict China app whitelist config.")
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
