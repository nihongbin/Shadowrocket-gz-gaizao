#!/usr/bin/env python3
"""Check health of S1.1 AI domain seed and candidate lists."""

from __future__ import annotations

import argparse
import datetime as dt
import http.client
import socket
import ssl
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEEDS = ROOT / "references" / "ai-proxy-domain-seeds.txt"
DEFAULT_CANDIDATES = ROOT / "references" / "ai-proxy-domain-candidates.txt"
DEFAULT_REPORT = ROOT / "docs" / "ai-domain-health-report.md"
CHECKABLE_TYPES = {"DOMAIN", "DOMAIN-SUFFIX"}
HTTP_OK_STATUSES = {200, 201, 202, 204, 301, 302, 307, 308, 401, 403, 404, 405, 429}


def strip_inline_comment(line: str) -> str:
    if not line or line.lstrip().startswith("#"):
        return ""
    return line.split("#", 1)[0].strip()


def parse_rules(path: Path, list_name: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        cleaned = strip_inline_comment(raw)
        if not cleaned:
            continue
        parts = [part.strip() for part in cleaned.split(",") if part.strip()]
        if len(parts) < 2:
            rows.append({"list": list_name, "type": "MALFORMED", "value": cleaned, "line": str(line_number)})
            continue
        rows.append({"list": list_name, "type": parts[0].upper(), "value": parts[1].lower(), "line": str(line_number)})
    return rows


def check_domain(domain: str) -> tuple[str, str]:
    try:
        answers = socket.getaddrinfo(domain, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        return "FAIL", f"DNS failed: {exc}"
    if not answers:
        return "FAIL", "DNS returned no answers"

    try:
        with socket.create_connection((domain, 443), timeout=8):
            pass
    except OSError as exc:
        return "FAIL", f"TCP 443 failed: {exc}"

    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=8) as sock:
            with context.wrap_socket(sock, server_hostname=domain):
                pass
    except OSError as exc:
        return "FAIL", f"TLS failed: {exc}"

    try:
        conn = http.client.HTTPSConnection(domain, 443, timeout=8)
        conn.request("HEAD", "/", headers={"User-Agent": "s1-1-ai-health/1.0"})
        response = conn.getresponse()
        status = response.status
        conn.close()
        if status in HTTP_OK_STATUSES or 300 <= status < 500:
            return "OK", f"HTTPS reachable, status {status}"
        return "WARN", f"HTTPS returned status {status}"
    except Exception as exc:  # noqa: BLE001 - HTTP probing intentionally handles broad network failures.
        return "WARN", f"HTTPS HEAD inconclusive: {exc}"


def render_report(rows: list[dict[str, str]]) -> str:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# S1.1 AI Domain Health Report",
        "",
        f"Generated: {now}",
        "",
        "This report is advisory. It does not automatically add, remove, or promote domains.",
        "",
        "| List | Rule | Status | Detail |",
        "|---|---|---|---|",
    ]
    for row in rows:
        rule = f"{row['type']},{row['value']}"
        if row["type"] not in CHECKABLE_TYPES:
            status, detail = "NOT_CHECKABLE", "Keyword or unsupported rule type is syntax-only."
        else:
            status, detail = check_domain(row["value"])
        escaped_detail = detail.replace("|", "\\|")
        lines.append(f"| {row['list']} | `{rule}` | `{status}` | {escaped_detail} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check S1.1 AI domain health.")
    parser.add_argument("--seeds", type=Path, default=DEFAULT_SEEDS)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    rows = parse_rules(args.seeds, "seeds") + parse_rules(args.candidates, "candidates")
    report = render_report(rows)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report, encoding="utf-8", newline="\n")
    print(f"wrote: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
