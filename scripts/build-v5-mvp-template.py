#!/usr/bin/env python3
"""Build the V5 MVP public Shadowrocket scenario template.

The private V5 config is the verified baseline, but it contains private proxy
sections in user workflows. This script extracts only [General], [Rule], and
[Host] logic into maintainable manifests, then rebuilds a public template from
those manifests.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
from collections import OrderedDict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_PATH = ROOT / "local" / "private-configs" / "S1-default-lazy-proxy-doh-1-stable-enhanced-cnapp-v5.conf"
EXPECTED_BASE_SHA256 = "D0478F6D913942FCF80DDC2D87650F98B50D7AC7E2D0AF49766C22804988F9DD"
DEFAULT_MANIFEST_DIR = ROOT / "references" / "v5-mvp"
DEFAULT_OUTPUT_PATH = ROOT / "configs" / "S5-scenario-cn-us-v5-mvp-v0.conf"

SENSITIVE_PATTERNS = re.compile(
    r"(ss://|ssr://|vmess://|vless://|trojan://|hysteria://)"
    r"|(\b(token|password|secret|subscribe|subscription(?:-url)?|api[-_]?key|username)\b\s*[=:])",
    re.IGNORECASE,
)

REQUIRED_GENERAL_SETTINGS = {
    "ipv6": "false",
    "prefer-ipv6": "false",
    "dns-server": (
        "https://cloudflare-dns.com/dns-query#proxy, "
        "https://security.cloudflare-dns.com/dns-query#proxy"
    ),
    "fallback-dns-server": (
        "https://cloudflare-dns.com/dns-query#proxy, "
        "https://security.cloudflare-dns.com/dns-query#proxy"
    ),
    "dns-direct-system": "false",
    "dns-fallback-system": "false",
    "dns-direct-fallback-proxy": "true",
    "hijack-dns": "8.8.8.8:53, 8.8.4.4:53",
    "block-quic": "all-proxy",
}

MANIFEST_BUILD_INPUTS = (
    "source-metadata.txt",
    "general.txt",
    "test-site-proxy-rules.txt",
    "overseas-proxy-rules.txt",
    "ai-proxy-rules.txt",
    "china-direct-domains.txt",
    "china-host-dns.csv",
    "remote-rulesets.csv",
    "lazy-body-rules.txt",
)

RULE_TYPES_WITH_POLICY = {
    "DOMAIN",
    "DOMAIN-SUFFIX",
    "DOMAIN-KEYWORD",
    "DOMAIN-WILDCARD",
    "IP-CIDR",
    "IP-CIDR6",
    "RULE-SET",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def parse_config(text: str) -> tuple[list[str], "OrderedDict[str, list[str]]"]:
    preamble: list[str] = []
    sections: "OrderedDict[str, list[str]]" = OrderedDict()
    current: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            current = stripped[1:-1].strip()
            sections.setdefault(current, [])
            continue
        if current is None:
            preamble.append(line)
        else:
            sections[current].append(line)
    return preamble, sections


def split_rule(line: str) -> list[str]:
    return [part.strip() for part in line.split(",") if part.strip()]


def strip_comment(line: str) -> str:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return ""
    return stripped.split("#", 1)[0].strip()


def unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            output.append(item)
    return output


def write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8", newline="\n")


def read_manifest_lines(path: Path) -> list[str]:
    output: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        output.append(line)
    return output


def manifest_revision(manifest_dir: Path) -> str:
    digest = hashlib.sha256()
    for name in MANIFEST_BUILD_INPUTS:
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update((manifest_dir / name).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest().upper()


def parse_host_dns(lines: list[str]) -> OrderedDict[str, str]:
    result: OrderedDict[str, str] = OrderedDict()
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "," in line:
            domain, server = [part.strip() for part in line.split(",", 1)]
        elif "=" in line and "server:" in line:
            domain, server = [part.strip() for part in line.split("=", 1)]
            server = server.replace("server:", "").strip()
        else:
            raise ValueError(f"malformed host dns line: {line}")
        domain = domain.lower().lstrip("*.").strip(".")
        if not domain or "." not in domain:
            raise ValueError(f"malformed host domain: {line}")
        if not server:
            raise ValueError(f"missing host dns server: {line}")
        result[domain] = server
    return result


def read_host_dns(path: Path) -> OrderedDict[str, str]:
    return parse_host_dns(path.read_text(encoding="utf-8").splitlines())


def read_ruleset_registry(path: Path) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split(",", 2)]
        if len(parts) != 3:
            raise ValueError(f"malformed remote ruleset row: {line}")
        policy, name, url = parts
        if policy not in {"DIRECT", "PROXY"}:
            raise ValueError(f"unsupported ruleset policy: {line}")
        if not url.startswith("https://"):
            raise ValueError(f"ruleset URL must be https: {line}")
        rows.append((policy, name, url))
    return rows


def validate_rule(rule: str, expected_policy: str | None = None) -> None:
    parts = split_rule(rule)
    if not parts:
        raise ValueError("empty rule")
    rule_type = parts[0].upper()
    if rule_type == "FINAL":
        if rule != "FINAL,PROXY":
            raise ValueError(f"unsupported FINAL rule: {rule}")
        return
    if rule_type == "GEOIP":
        if rule != "GEOIP,CN,DIRECT":
            raise ValueError(f"unsupported GEOIP rule: {rule}")
        return
    if rule_type not in RULE_TYPES_WITH_POLICY:
        raise ValueError(f"unsupported rule type: {rule}")
    if len(parts) < 3:
        raise ValueError(f"malformed rule: {rule}")
    policy = parts[2].upper()
    if policy not in {"DIRECT", "PROXY"}:
        raise ValueError(f"unsupported rule policy: {rule}")
    if expected_policy and policy != expected_policy:
        raise ValueError(f"expected {expected_policy} rule, got: {rule}")


def section_header(title: str) -> list[str]:
    return ["", f"# {title}"]


def extract_manifests(base_path: Path, manifest_dir: Path) -> dict[str, int]:
    actual_sha = sha256_file(base_path)
    if actual_sha != EXPECTED_BASE_SHA256:
        raise ValueError(
            "V5 base hash mismatch: "
            f"expected {EXPECTED_BASE_SHA256}, got {actual_sha}"
        )

    _, sections = parse_config(base_path.read_text(encoding="utf-8-sig"))
    for name in ("General", "Rule", "Host"):
        if name not in sections:
            raise ValueError(f"base config missing [{name}]")

    general = [line.rstrip() for line in sections["General"]]
    rule = [line.rstrip() for line in sections["Rule"]]
    host = [line.rstrip() for line in sections["Host"]]

    test_rules: list[str] = []
    overseas_rules: list[str] = []
    ai_rules: list[str] = []
    china_domains: list[str] = []
    lazy_body_rules: list[str] = []
    remote_rulesets: list[tuple[str, str, str]] = []

    current = None
    in_lazy = False
    for line in rule:
        stripped = line.strip()
        if stripped.startswith("# DNS/IP test-site guard"):
            current = "test"
            continue
        if stripped.startswith("# Account/AI/media guard"):
            current = "overseas"
            continue
        if stripped.startswith("# Stable enhanced overseas/common guard"):
            current = "overseas"
            continue
        if stripped.startswith("# Stable enhanced AI guard"):
            current = "ai"
            continue
        if stripped.startswith("# China-local guard"):
            current = "china"
            continue
        if stripped.startswith("# V4 China App"):
            current = "china"
            continue
        if stripped.startswith("# V5 China App"):
            current = "china"
            continue
        if stripped.startswith("# Johnshall lazy.conf"):
            current = "lazy"
            in_lazy = True
            continue

        cleaned = strip_comment(stripped)
        if not cleaned:
            continue
        if cleaned in {"GEOIP,CN,DIRECT", "FINAL,PROXY"}:
            continue

        if current == "test":
            validate_rule(cleaned, expected_policy="PROXY")
            test_rules.append(cleaned)
        elif current == "overseas":
            validate_rule(cleaned, expected_policy="PROXY")
            overseas_rules.append(cleaned)
        elif current == "ai":
            validate_rule(cleaned, expected_policy="PROXY")
            ai_rules.append(cleaned)
        elif current == "china":
            validate_rule(cleaned, expected_policy="DIRECT")
            parts = split_rule(cleaned)
            if parts[0].upper() != "DOMAIN-SUFFIX":
                raise ValueError(f"China DIRECT manifest only supports DOMAIN-SUFFIX: {cleaned}")
            china_domains.append(parts[1].lower())
        elif in_lazy:
            validate_rule(cleaned)
            lazy_body_rules.append(cleaned)
            parts = split_rule(cleaned)
            if parts[0].upper() == "RULE-SET":
                url = parts[1]
                policy = parts[2].upper()
                name = url.split("/Shadowrocket/")[-1].replace(".list", "")
                remote_rulesets.append((policy, name, url))
        else:
            raise ValueError(f"unclassified rule line: {cleaned}")

    host_dns: OrderedDict[str, str] = OrderedDict()
    wildcard_seen: set[str] = set()
    for line in host:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped == "localhost = 127.0.0.1":
            continue
        if " = server:" not in stripped:
            raise ValueError(f"unsupported Host line: {stripped}")
        domain, server = [part.strip() for part in stripped.split("=", 1)]
        server = server.replace("server:", "").strip()
        normalized = domain.lower().lstrip("*.").strip(".")
        if domain.startswith("*."):
            wildcard_seen.add(normalized)
            continue
        host_dns[normalized] = server

    china_domains = unique_preserve_order(china_domains)
    if set(china_domains) != set(host_dns.keys()):
        missing_host = sorted(set(china_domains) - set(host_dns.keys()))
        extra_host = sorted(set(host_dns.keys()) - set(china_domains))
        raise ValueError(
            "China DIRECT and Host DNS manifests differ: "
            f"missing_host={missing_host[:10]}, extra_host={extra_host[:10]}"
        )
    missing_wildcard = sorted(set(china_domains) - wildcard_seen)
    if missing_wildcard:
        raise ValueError(f"Host DNS missing wildcard entries: {missing_wildcard[:10]}")

    write_lines(manifest_dir / "source-metadata.txt", [
        "# V5 MVP source metadata. Stable values only; do not write runtime timestamps.",
        f"base_path=local/private-configs/S1-default-lazy-proxy-doh-1-stable-enhanced-cnapp-v5.conf",
        f"base_sha256={actual_sha}",
    ])
    write_lines(manifest_dir / "general.txt", [
        "# V5 [General] settings copied from the verified private baseline.",
        "# Do not add DNS B, QUIC allow, or other discarded variables here.",
        *general,
    ])
    write_lines(manifest_dir / "test-site-proxy-rules.txt", [
        "# DNS/IP test sites must stay PROXY and before China DIRECT.",
        *unique_preserve_order(test_rules),
    ])
    write_lines(manifest_dir / "overseas-proxy-rules.txt", [
        "# Overseas account, media, SDK, and common service guard rules.",
        "# Keep these before China DIRECT.",
        *unique_preserve_order(overseas_rules),
    ])
    write_lines(manifest_dir / "ai-proxy-rules.txt", [
        "# AI and AI-adjacent service guard rules.",
        "# Keep these before China DIRECT.",
        *unique_preserve_order(ai_rules),
    ])
    write_lines(manifest_dir / "china-direct-domains.txt", [
        "# China App / China service domains allowed to DIRECT.",
        "# Every domain here must also exist in china-host-dns.csv.",
        *china_domains,
    ])
    write_lines(manifest_dir / "china-host-dns.csv", [
        "# domain,dns_server",
        *[f"{domain},{server}" for domain, server in host_dns.items()],
    ])
    write_lines(manifest_dir / "remote-rulesets.csv", [
        "# policy,name,url",
        *[f"{policy},{name},{url}" for policy, name, url in remote_rulesets],
    ])
    write_lines(manifest_dir / "lazy-body-rules.txt", [
        "# Full V5 lazy body rules in original order.",
        "# Keep this file in sync with remote-rulesets.csv when changing RULE-SET entries.",
        *unique_preserve_order(lazy_body_rules),
    ])
    write_lines(manifest_dir / "candidate-observations.md", [
        "# V5 MVP Candidate Observations",
        "",
        "- Do not add `itdog.cn`, `ip.cn`, DNS leak test sites, or IP lookup sites to China DIRECT.",
        "- Do not use DNS B Google fallback as a V5 baseline; the fallback was not triggered in the test logs.",
        "- Do not use QUIC allow as a V5 baseline; it did not prove a speed improvement.",
        "- If an overseas App is slow only on first open and fast on second open, prefer network/node/time-window checks before rules.",
        "- If a new China App domain is added to DIRECT, add the same root domain to `china-host-dns.csv`.",
    ])
    write_lines(manifest_dir / "README.md", [
        "# V5 MVP Manifests",
        "",
        "These files are the maintainable source of the public S5 V5 MVP template.",
        "The verified private V5 config is used only as the bootstrap source; do not commit private nodes or proxy groups.",
        "",
        "- `general.txt`: V5 `[General]` settings, without nodes or proxy groups.",
        "- `test-site-proxy-rules.txt`: DNS/IP test sites forced to `PROXY`.",
        "- `overseas-proxy-rules.txt`: overseas account, media, SDK, and common service `PROXY` rules.",
        "- `ai-proxy-rules.txt`: AI and AI-adjacent `PROXY` rules.",
        "- `china-direct-domains.txt`: China App / China service domains allowed to `DIRECT`.",
        "- `china-host-dns.csv`: China Host DNS mapping. Must contain every China DIRECT domain.",
        "- `remote-rulesets.csv`: remote `RULE-SET` registry used by V5.",
        "- `lazy-body-rules.txt`: full V5 lazy body rule order used by the generated template.",
        "- `candidate-observations.md`: excluded or watch-only items.",
        "- `upstream-sources.md`: upstream attribution, license, and runtime dependency notes.",
        "",
        "Build the public template with:",
        "",
        "```powershell",
        "python scripts\\build-v5-mvp-template.py",
        "```",
        "",
        "Verify the public template and local V5 baseline with:",
        "",
        "```powershell",
        "python scripts\\build-v5-mvp-template.py --check",
        "python scripts\\check-v5-consistency.py",
        "```",
    ])

    return {
        "test_proxy": len(test_rules),
        "overseas_proxy": len(overseas_rules),
        "ai_proxy": len(ai_rules),
        "china_direct": len(china_domains),
        "host_dns": len(host_dns),
        "remote_rulesets": len(remote_rulesets),
        "lazy_body": len(lazy_body_rules),
    }


def read_source_metadata(manifest_dir: Path) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for raw in (manifest_dir / "source-metadata.txt").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"malformed source metadata: {line}")
        key, value = line.split("=", 1)
        metadata[key.strip()] = value.strip()
    if metadata.get("base_sha256") != EXPECTED_BASE_SHA256:
        raise ValueError("source metadata does not match expected V5 SHA256")
    return metadata


def build_template(manifest_dir: Path) -> str:
    metadata = read_source_metadata(manifest_dir)
    general = read_manifest_lines(manifest_dir / "general.txt")
    test_rules = read_manifest_lines(manifest_dir / "test-site-proxy-rules.txt")
    overseas_rules = read_manifest_lines(manifest_dir / "overseas-proxy-rules.txt")
    ai_rules = read_manifest_lines(manifest_dir / "ai-proxy-rules.txt")
    china_domains = read_manifest_lines(manifest_dir / "china-direct-domains.txt")
    host_dns = read_host_dns(manifest_dir / "china-host-dns.csv")
    remote_rulesets = read_ruleset_registry(manifest_dir / "remote-rulesets.csv")
    lazy_body_rules = read_manifest_lines(manifest_dir / "lazy-body-rules.txt")

    for rule in [*test_rules, *overseas_rules, *ai_rules]:
        validate_rule(rule, expected_policy="PROXY")
    for rule in lazy_body_rules:
        validate_rule(rule)

    body_rulesets = [
        (split_rule(rule)[2].upper(), split_rule(rule)[1])
        for rule in lazy_body_rules
        if split_rule(rule)[0].upper() == "RULE-SET"
    ]
    registry_rulesets = [(policy, url) for policy, _name, url in remote_rulesets]
    if body_rulesets != registry_rulesets:
        raise ValueError("lazy-body-rules.txt and remote-rulesets.csv RULE-SET order differ")

    for domain in china_domains:
        if domain not in host_dns:
            raise ValueError(f"China DIRECT domain missing Host DNS: {domain}")
    extra_host = sorted(set(host_dns.keys()) - set(china_domains))
    if extra_host:
        raise ValueError(f"Host DNS has domains not in China DIRECT: {extra_host[:10]}")

    header = [
        "# Shadowrocket S5 V5 MVP public scenario template",
        "# This file contains rules, DNS, and Host logic only.",
        "# It does not contain proxy nodes, subscriptions, accounts, proxy groups, or secrets.",
        "# Derived in part from Johnshall lazy.conf and blackmatrix7 ios_rule_script sources.",
        "# License: CC BY-SA 4.0. See LICENSE and references/v5-mvp/upstream-sources.md.",
        f"# source_private_base_sha256={metadata['base_sha256']}",
        f"# manifest_revision={manifest_revision(manifest_dir)}",
        f"# counts: test_proxy={len(test_rules)}, overseas_proxy={len(overseas_rules)}, ai_proxy={len(ai_rules)}, china_direct={len(china_domains)}, remote_rulesets={len(remote_rulesets)}",
        "# Generated from references/v5-mvp manifests. No runtime timestamp is written.",
        "",
    ]

    rule_lines: list[str] = []
    rule_lines.extend(section_header("DNS/IP test-site guard: keep leak-test pages on PROXY before any DIRECT fallback."))
    rule_lines.extend(test_rules)
    rule_lines.extend(section_header("Account/media/common-service guard: keep overseas accounts on PROXY before China DIRECT."))
    rule_lines.extend(overseas_rules)
    rule_lines.extend(section_header("AI guard: keep overseas AI and AI-adjacent services on PROXY."))
    rule_lines.extend(ai_rules)
    rule_lines.extend(section_header("China App / China service DIRECT guard."))
    rule_lines.extend([f"DOMAIN-SUFFIX,{domain},DIRECT" for domain in china_domains])
    rule_lines.extend(section_header("Johnshall lazy body inherited from V5."))
    rule_lines.extend(lazy_body_rules)
    rule_lines.extend(["GEOIP,CN,DIRECT", "FINAL,PROXY"])

    host_lines = [
        "# China-local Host DNS mapping. China DIRECT domains use explicit DNS for better local CDN selection.",
        "localhost = 127.0.0.1",
    ]
    for domain, server in host_dns.items():
        host_lines.append(f"{domain} = server:{server}")
        host_lines.append(f"*.{domain} = server:{server}")

    output = [
        *header,
        "[General]",
        *general,
        "",
        "[Rule]",
        *rule_lines,
        "",
        "[Host]",
        *host_lines,
        "",
    ]
    rendered = "\n".join(output).rstrip() + "\n"
    validate_public_template(rendered)
    return rendered


def extract_rule_section(text: str) -> list[str]:
    _, sections = parse_config(text)
    return sections.get("Rule", [])


def last_effective_rule(text: str) -> str:
    for line in reversed(extract_rule_section(text)):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return ""


def validate_public_template(text: str) -> None:
    _, sections = parse_config(text)
    for name in ("General", "Rule", "Host"):
        if name not in sections:
            raise ValueError(f"public template missing [{name}]")
    if any(name in sections for name in ("Proxy", "Proxy Group", "MITM", "URL Rewrite")):
        raise ValueError("public template contains private or unsupported sections")
    if SENSITIVE_PATTERNS.search(text):
        raise ValueError("public template contains sensitive-looking content")
    if "server:system" in text.lower():
        raise ValueError("public template must not use server:system")

    general_settings: dict[str, str] = {}
    for raw in sections["General"]:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        normalized_key = key.lower()
        if normalized_key in general_settings:
            raise ValueError(f"duplicate [General] setting: {key}")
        general_settings[normalized_key] = value
    for key, expected in REQUIRED_GENERAL_SETTINGS.items():
        actual = general_settings.get(key)
        if actual != expected:
            raise ValueError(
                f"unsafe [General] setting {key}: expected {expected!r}, got {actual!r}"
            )
    if "dns.google/dns-query#proxy" in text:
        raise ValueError("DNS B Google fallback must not enter V5 MVP")
    if "block-quic = always-allow" in text:
        raise ValueError("QUIC allow must not enter V5 MVP")
    if last_effective_rule(text) != "FINAL,PROXY":
        raise ValueError("[Rule] last effective rule must be FINAL,PROXY")

    rule_text = "\n".join(sections["Rule"])
    test_index = rule_text.find("DOMAIN-SUFFIX,browserleaks.com,PROXY")
    overseas_index = rule_text.find("DOMAIN-SUFFIX,youtube.com,PROXY")
    china_index = rule_text.find("DOMAIN-SUFFIX,wechat.com,DIRECT")
    remote_index = rule_text.find("RULE-SET,")
    if min(test_index, overseas_index, china_index, remote_index) < 0:
        raise ValueError("public template missing key guard rules")
    if not (test_index < china_index and overseas_index < china_index < remote_index):
        raise ValueError("public template rule order is unsafe")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build S5 V5 MVP public scenario template.")
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE_PATH, help="Verified private V5 baseline.")
    parser.add_argument("--manifest-dir", type=Path, default=DEFAULT_MANIFEST_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--sync-manifests", action="store_true", help="Extract manifests from the verified V5 baseline first.")
    parser.add_argument("--check", action="store_true", help="Validate generated output without writing it.")
    args = parser.parse_args()

    try:
        if args.sync_manifests:
            stats = extract_manifests(args.base.resolve(), args.manifest_dir.resolve())
            print("synced_manifests=" + ",".join(f"{key}:{value}" for key, value in stats.items()))

        rendered = build_template(args.manifest_dir.resolve())
        output_path = args.output.resolve()

        if args.check:
            if not output_path.exists():
                print(f"output is missing: {output_path}", file=sys.stderr)
                return 4
            current = output_path.read_text(encoding="utf-8")
            if current != rendered:
                print(f"output differs from generated template: {output_path}", file=sys.stderr)
                return 4
            print("check=PASS")
            print("output_sha256=" + hashlib.sha256(rendered.encode("utf-8")).hexdigest().upper())
            return 0

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8", newline="\n")
        print(f"wrote_public_template={output_path}")
        print("output_sha256=" + sha256_file(output_path))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
