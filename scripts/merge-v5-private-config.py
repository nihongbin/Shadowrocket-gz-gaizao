#!/usr/bin/env python3
"""Merge private proxy sections with the governed public S5 template."""

from __future__ import annotations

import argparse
import sys
from collections import OrderedDict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "configs" / "S5-scenario-cn-us-v5-mvp-v0.conf"
PRIVATE_ROOT = ROOT / "local" / "private-configs"
REQUIRED_TEMPLATE_SECTIONS = ("General", "Rule", "Host")
PRIVATE_SECTIONS = ("Proxy", "Proxy Group")


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


def effective_lines(lines: list[str]) -> list[str]:
    return [
        line.strip()
        for line in lines
        if line.strip() and not line.lstrip().startswith("#")
    ]


def render_section(name: str, lines: list[str]) -> list[str]:
    return [f"[{name}]", *lines]


def last_effective_rule(text: str) -> str:
    _, sections = parse_config(text)
    rules = effective_lines(sections.get("Rule", []))
    return rules[-1] if rules else ""


def validate_template(sections: "OrderedDict[str, list[str]]") -> None:
    missing = [name for name in REQUIRED_TEMPLATE_SECTIONS if name not in sections]
    if missing:
        raise ValueError(f"S5 template missing sections: {', '.join(missing)}")
    forbidden = [name for name in (*PRIVATE_SECTIONS, "MITM", "URL Rewrite") if name in sections]
    if forbidden:
        raise ValueError(f"S5 template contains forbidden sections: {', '.join(forbidden)}")


def validate_base(sections: "OrderedDict[str, list[str]]") -> None:
    for name in PRIVATE_SECTIONS:
        if name not in sections or not effective_lines(sections[name]):
            raise ValueError(f"base config missing non-empty [{name}]")

    # S5 的规则统一引用 PROXY；没有同名策略组时，合并文件会导入成功但无法联网。
    group_names = {
        line.split("=", 1)[0].strip()
        for line in effective_lines(sections["Proxy Group"])
        if "=" in line
    }
    if "PROXY" not in group_names:
        raise ValueError("base config must define a [Proxy Group] named PROXY")


def merge_configs(base_text: str, template_text: str) -> str:
    _, base_sections = parse_config(base_text)
    _, template_sections = parse_config(template_text)
    validate_base(base_sections)
    validate_template(template_sections)

    output: list[str] = [
        "# PRIVATE V5 MERGED CONFIG",
        "# Contains proxy nodes copied from the local base config.",
        "# Keep this file under local/private-configs and never publish it.",
        "",
    ]

    output.extend(render_section("General", template_sections["General"]))
    output.append("")
    for name in PRIVATE_SECTIONS:
        output.extend(render_section(name, base_sections[name]))
        output.append("")
    output.extend(render_section("Rule", template_sections["Rule"]))
    output.append("")
    output.extend(render_section("Host", template_sections["Host"]))
    output.append("")

    merged = "\n".join(output).rstrip() + "\n"
    if last_effective_rule(merged) != "FINAL,PROXY":
        raise ValueError("merged [Rule] must end with FINAL,PROXY")
    return merged


def validate_output_path(path: Path) -> Path:
    resolved = path.resolve()
    private_root = PRIVATE_ROOT.resolve()
    try:
        resolved.relative_to(private_root)
    except ValueError as exc:
        raise ValueError("private output must stay under local/private-configs") from exc
    if resolved == private_root or resolved.suffix.lower() != ".conf":
        raise ValueError("private output must be a .conf file under local/private-configs")
    return resolved


def section_summary(text: str) -> str:
    _, sections = parse_config(text)
    return ",".join(f"{name}:{len(effective_lines(lines))}" for name, lines in sections.items())


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Merge a complete private Shadowrocket config with the governed S5 template."
    )
    parser.add_argument("--base", type=Path, required=True, help="Complete local config with [Proxy] and [Proxy Group].")
    parser.add_argument("--output", type=Path, help="Output .conf under local/private-configs/.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print section counts without writing.")
    args = parser.parse_args()

    try:
        base_text = read_text(args.base.resolve())
        template_text = read_text(TEMPLATE_PATH)
        merged = merge_configs(base_text, template_text)
        print("base_sections=" + section_summary(base_text))
        print("template_sections=" + section_summary(template_text))
        print("merged_sections=" + section_summary(merged))

        if args.dry_run:
            print("dry_run=PASS")
            return 0
        if args.output is None:
            print("missing --output for non-dry-run merge", file=sys.stderr)
            return 2

        output_path = validate_output_path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(merged, encoding="utf-8", newline="\n")
        print(f"wrote_private_config={output_path}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
