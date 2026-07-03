#!/usr/bin/env python3
"""Merge private Shadowrocket proxy sections with a public scenario template.

The public S0/S1/S5 configs intentionally have no proxy nodes. This script builds a
private full config by keeping proxy-related sections from a user's original
complete config and replacing only [General], [Host], and [Rule] with the
selected scenario template.
"""

from __future__ import annotations

import argparse
import sys
import re
from collections import OrderedDict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_S0_PATH = ROOT / "configs" / "S0-scenario-cn-us-account-aggressive-v0.conf"
DEFAULT_S5_PATH = ROOT / "configs" / "S5-scenario-cn-us-v5-mvp-v0.conf"
LOCAL_PRIVATE_OUTPUT_ROOT = ROOT / "local" / "private-configs"
REPLACE_SECTIONS = ("General", "Host", "Rule")
PRESERVE_BASE_SECTIONS = ("Proxy", "Proxy Group")
QUIC_BLOCK_RULE = "AND,((PROTOCOL,UDP),(DEST-PORT,443)),REJECT-NO-DROP"


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


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


def render_section(name: str, lines: list[str]) -> list[str]:
    return [f"[{name}]", *lines]


def upsert_general_setting(lines: list[str], key: str, value: str) -> list[str]:
    pattern = re.compile(rf"^(\s*){re.escape(key)}\s*=", re.IGNORECASE)
    output = list(lines)
    for index, line in enumerate(output):
        match = pattern.match(line)
        if match:
            output[index] = f"{match.group(1)}{key} = {value}"
            return output
    output.append(f"{key} = {value}")
    return output


def build_plain_us_dns_general(base_lines: list[str]) -> list[str]:
    output = list(base_lines)
    output = upsert_general_setting(output, "dns-server", "8.8.8.8, 1.1.1.1")
    output = upsert_general_setting(output, "fallback-dns-server", "8.8.8.8, 1.1.1.1")
    output = upsert_general_setting(output, "dns-direct-system", "false")
    output = upsert_general_setting(output, "dns-fallback-system", "false")
    output = upsert_general_setting(output, "dns-direct-fallback-proxy", "true")
    return output


def build_proxy_doh_general(base_lines: list[str]) -> list[str]:
    proxy_doh = (
        "https://cloudflare-dns.com/dns-query#proxy, "
        "https://security.cloudflare-dns.com/dns-query#proxy"
    )
    output = list(base_lines)
    output = upsert_general_setting(output, "dns-server", proxy_doh)
    output = upsert_general_setting(output, "fallback-dns-server", proxy_doh)
    output = upsert_general_setting(output, "dns-direct-system", "false")
    output = upsert_general_setting(output, "dns-fallback-system", "false")
    output = upsert_general_setting(output, "dns-direct-fallback-proxy", "true")
    return output


def build_rule_lines(rule_lines: list[str], block_quic: bool = False) -> list[str]:
    output = list(rule_lines)
    if not block_quic or QUIC_BLOCK_RULE in output:
        return output
    return [
        "# Media test: block QUIC/HTTP3 over UDP 443 to reduce streaming slowdown through proxy.",
        QUIC_BLOCK_RULE,
        "",
        *output,
    ]


def merge_configs(
    base_text: str,
    template_text: str,
    preserve_general: bool = False,
    plain_us_dns: bool = False,
    proxy_doh: bool = False,
    block_quic: bool = False,
) -> str:
    base_preamble, base_sections = parse_config(base_text)
    _, template_sections = parse_config(template_text)

    missing = [name for name in REPLACE_SECTIONS if name not in template_sections]
    if missing:
        raise ValueError(f"scenario template missing required sections: {', '.join(missing)}")

    output: list[str] = [
        "# PRIVATE SCENARIO MERGED CONFIG",
        "# This file may contain proxy nodes copied from your original config.",
        "# Do not commit, publish, paste, or upload this file.",
        "# Public scenario template replaces only [General], [Host], and [Rule].",
        "# Only [Proxy] and [Proxy Group] are preserved from the original config.",
        "",
    ]

    if base_preamble:
        output.extend(base_preamble)
        output.append("")

    # Shadowrocket 只能选一个配置文件。私有合并版固定为：
    # General -> 原始节点/代理组私有段 -> 模板 Host -> 模板 Rule。
    # 这样既保留节点，又让最终兜底规则保持在文件末尾。
    if proxy_doh:
        if "General" not in base_sections:
            raise ValueError("base config missing [General], cannot build proxy DoH mode")
        output.extend(render_section("General", build_proxy_doh_general(base_sections["General"])))
    elif plain_us_dns:
        if "General" not in base_sections:
            raise ValueError("base config missing [General], cannot build plain US DNS mode")
        output.extend(render_section("General", build_plain_us_dns_general(base_sections["General"])))
    elif preserve_general:
        if "General" not in base_sections:
            raise ValueError("base config missing [General], cannot preserve it")
        output.extend(render_section("General", base_sections["General"]))
    else:
        output.extend(render_section("General", template_sections["General"]))
    output.append("")

    for name, lines in base_sections.items():
        if name in REPLACE_SECTIONS:
            continue
        if name not in PRESERVE_BASE_SECTIONS:
            continue
        output.extend(render_section(name, lines))
        output.append("")

    output.extend(render_section("Host", template_sections["Host"]))
    output.append("")
    output.extend(render_section("Rule", build_rule_lines(template_sections["Rule"], block_quic=block_quic)))
    output.append("")

    return "\n".join(output).rstrip() + "\n"


def section_summary(text: str) -> list[str]:
    _, sections = parse_config(text)
    return [f"{name}:{len(lines)}" for name, lines in sections.items()]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a private complete Shadowrocket config from a base config and public scenario template."
    )
    parser.add_argument("--base", type=Path, required=True, help="Original complete Shadowrocket config.")
    parser.add_argument(
        "--template",
        type=Path,
        help="Public S0/S1 scenario template. Defaults to the S0 template for compatibility.",
    )
    parser.add_argument(
        "--s0",
        type=Path,
        help="Backward-compatible alias for --template.",
    )
    parser.add_argument(
        "--v5-mvp",
        action="store_true",
        help="Use the public S5 V5 MVP template.",
    )
    parser.add_argument("--output", type=Path, help="Private merged output path outside this repo.")
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs and print section summary only.")
    parser.add_argument(
        "--preserve-general",
        action="store_true",
        help="Keep [General] from the base config and replace only [Host] and [Rule] with the template.",
    )
    parser.add_argument(
        "--plain-us-dns",
        action="store_true",
        help="Use base [General] but set default DNS to 8.8.8.8 / 1.1.1.1 and keep template [Host]/[Rule].",
    )
    parser.add_argument(
        "--proxy-doh",
        action="store_true",
        help="Use base [General] but set default DoH to Cloudflare/security.cloudflare with #proxy.",
    )
    parser.add_argument(
        "--block-quic",
        action="store_true",
        help="Insert a UDP 443 QUIC/HTTP3 reject rule before S0 account guard rules.",
    )
    parser.add_argument(
        "--allow-output-in-repo",
        action="store_true",
        help="Unsafe escape hatch for local debugging only. Do not use with real nodes.",
    )
    args = parser.parse_args()

    selected_modes = [args.preserve_general, args.plain_us_dns, args.proxy_doh]
    if sum(1 for selected in selected_modes if selected) > 1:
        print("choose only one: --preserve-general, --plain-us-dns, or --proxy-doh", file=sys.stderr)
        return 2

    base_path = args.base.resolve()
    if args.v5_mvp and (args.template or args.s0):
        print("choose either --v5-mvp or --template/--s0, not both", file=sys.stderr)
        return 2

    template_path = (DEFAULT_S5_PATH if args.v5_mvp else (args.template or args.s0 or DEFAULT_S0_PATH)).resolve()
    base_text = read_text(base_path)
    template_text = read_text(template_path)
    merged = merge_configs(
        base_text,
        template_text,
        preserve_general=args.preserve_general,
        plain_us_dns=args.plain_us_dns,
        proxy_doh=args.proxy_doh,
        block_quic=args.block_quic,
    )

    print("base_sections=" + ",".join(section_summary(base_text)))
    print("template_sections=" + ",".join(section_summary(template_text)))
    print("merged_sections=" + ",".join(section_summary(merged)))

    if args.dry_run:
        print("dry_run=PASS")
        return 0

    if not args.output:
        print("missing --output for non-dry-run merge", file=sys.stderr)
        return 2

    output_path = args.output.resolve()
    root = ROOT.resolve()
    local_private_root = LOCAL_PRIVATE_OUTPUT_ROOT.resolve()
    # 私有完整配置可以放在项目内，但只能放到已被 .gitignore 忽略的 local/private-configs。
    # 这样以后测试文件不再散落桌面，也避免误写进 configs/ 这类公开模板目录。
    if (
        is_relative_to(output_path, root)
        and not is_relative_to(output_path, local_private_root)
        and not args.allow_output_in_repo
    ):
        print(
            "refusing to write private merged config inside public project directories",
            file=sys.stderr,
        )
        print(f"project={root}", file=sys.stderr)
        print(f"allowed_private_output_root={local_private_root}", file=sys.stderr)
        print(f"output={output_path}", file=sys.stderr)
        return 3

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(merged, encoding="utf-8", newline="\n")
    print(f"wrote_private_config={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
