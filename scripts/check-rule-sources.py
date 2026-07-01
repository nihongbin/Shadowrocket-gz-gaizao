#!/usr/bin/env python3
"""Monitor S1.1 rule sources and write reports for GitHub Issue notification."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urldefrag


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "references" / "rule-source-registry.json"
DEFAULT_REPORT = ROOT / "docs" / "rule-source-health-report.md"
DEFAULT_LAZY_REPORT = ROOT / "docs" / "lazy-upstream-diff-report.md"
DEFAULT_JSON = ROOT / "local" / "rule-source-monitor-result.json"

HIGH_RISK_PATTERNS = {
    "MITM": re.compile(r"^\[MITM\]|\bMITM\b", re.IGNORECASE | re.MULTILINE),
    "URL Rewrite": re.compile(r"^\[URL Rewrite\]|\bURL Rewrite\b", re.IGNORECASE | re.MULTILINE),
    "server:system": re.compile(r"server:system", re.IGNORECASE),
    "dns-server system": re.compile(r"^\s*dns-server\s*=\s*system", re.IGNORECASE | re.MULTILINE),
    "fallback-dns-server system": re.compile(r"^\s*fallback-dns-server\s*=\s*system", re.IGNORECASE | re.MULTILINE),
    "QuantumultX path": re.compile(r"rule/QuantumultX/", re.IGNORECASE),
    "FINAL,DIRECT": re.compile(r"^FINAL\s*,\s*DIRECT", re.IGNORECASE | re.MULTILINE),
}

SEVERITY_ORDER = {"OK": 0, "P3": 1, "P2": 2, "P1": 3, "P0": 4}


def fetch_bytes(url: str) -> tuple[int | None, bytes, str | None]:
    fetch_url, _ = urldefrag(url)
    req = urllib.request.Request(fetch_url, headers={"User-Agent": "s1-1-source-monitor/1.0"})
    last_error: str | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return int(response.status), response.read(), None
        except urllib.error.HTTPError as exc:
            body = exc.read()
            return int(exc.code), body, None
        except Exception as exc:  # noqa: BLE001 - monitoring should report broad network failures.
            last_error = str(exc)
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
    return None, b"", last_error


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def load_sources(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("sources", []))


def classify_source(item: dict[str, object]) -> dict[str, object]:
    url = str(item["url"])
    kind = str(item.get("kind", ""))
    expected_sha = item.get("expected_sha256")
    status_code, content, error = fetch_bytes(url)
    findings: list[str] = []
    severity = "OK"
    current_sha: str | None = None

    if error or status_code is None:
        return {
            "id": item["id"],
            "url": url,
            "status": "P0",
            "summary": f"unreachable: {error}",
            "status_code": status_code,
            "current_sha256": None,
            "expected_sha256": expected_sha,
            "findings": ["source unreachable"],
        }

    if kind == "doh":
        if status_code >= 500:
            severity = "P0"
            findings.append(f"DoH endpoint returned {status_code}")
        return {
            "id": item["id"],
            "url": url,
            "status": severity,
            "summary": f"DoH reachable with HTTP {status_code}",
            "status_code": status_code,
            "current_sha256": None,
            "expected_sha256": expected_sha,
            "findings": findings,
        }

    if status_code != 200:
        severity = "P0"
        findings.append(f"HTTP {status_code}")
    if not content:
        severity = "P0"
        findings.append("empty content")

    current_sha = sha256_bytes(content)
    sha_changed = bool(expected_sha and current_sha != expected_sha)
    if kind == "reference-upstream" and expected_sha and not sha_changed:
        return {
            "id": item["id"],
            "url": url,
            "status": severity,
            "summary": "reference unchanged; excluded upstream sections are not adopted",
            "status_code": status_code,
            "current_sha256": current_sha,
            "expected_sha256": expected_sha,
            "findings": findings,
        }

    text = content.decode("utf-8", errors="ignore")
    for label, pattern in HIGH_RISK_PATTERNS.items():
        if pattern.search(text):
            severity = max_severity(severity, "P1")
            findings.append(label)

    if expected_sha and sha_changed:
        severity = max_severity(severity, "P2")
        findings.append("sha256 changed")
    elif not expected_sha:
        severity = max_severity(severity, "P3")
        findings.append("missing baseline hash")

    summary = "OK" if not findings else "; ".join(findings)
    return {
        "id": item["id"],
        "url": url,
        "status": severity,
        "summary": summary,
        "status_code": status_code,
        "current_sha256": current_sha,
        "expected_sha256": expected_sha,
        "findings": findings,
    }


def max_severity(left: str, right: str) -> str:
    return left if SEVERITY_ORDER[left] >= SEVERITY_ORDER[right] else right


def aggregate_severity(results: list[dict[str, object]]) -> str:
    severity = "OK"
    for item in results:
        severity = max_severity(severity, str(item["status"]))
    return severity


def render_health_report(results: list[dict[str, object]], severity: str) -> str:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# S1.1 Rule Source Health Report",
        "",
        f"Generated: {now}",
        f"Overall severity: `{severity}`",
        "",
        "| Source ID | Status | HTTP | Finding | URL |",
        "|---|---|---:|---|---|",
    ]
    for item in results:
        http = item["status_code"] if item["status_code"] is not None else "n/a"
        summary = str(item["summary"]).replace("|", "\\|")
        lines.append(f"| `{item['id']}` | `{item['status']}` | {http} | {summary} | {item['url']} |")
    lines.append("")
    lines.extend(
        [
            "## Approval Commands",
            "",
            "- `/approve-s1.1-update`",
            "- `/approve-source-update source-id`",
            "- `/reject-source-update source-id`",
            "",
        ]
    )
    return "\n".join(lines)


def render_lazy_report(results: list[dict[str, object]]) -> str:
    lazy = [item for item in results if item["id"] == "johnshall-lazy"]
    lines = [
        "# S1.1 Lazy Upstream Diff Report",
        "",
        "Johnshall lazy.conf is monitored as a reference source only. Changes do not automatically enter S1.1.",
        "",
    ]
    if not lazy:
        lines.append("- `johnshall-lazy` is missing from the registry.")
    else:
        item = lazy[0]
        lines.append(f"- Status: `{item['status']}`")
        lines.append(f"- Finding: {item['summary']}")
        lines.append(f"- Expected SHA256: `{item.get('expected_sha256') or 'n/a'}`")
        lines.append(f"- Current SHA256: `{item.get('current_sha256') or 'n/a'}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check S1.1 rule source health.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--lazy-report", type=Path, default=DEFAULT_LAZY_REPORT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    args = parser.parse_args()

    results = [classify_source(item) for item in load_sources(args.registry)]
    severity = aggregate_severity(results)
    payload = {
        "severity": severity,
        "issue_required": severity != "OK",
        "results": results,
    }

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_health_report(results, severity), encoding="utf-8", newline="\n")
    args.lazy_report.write_text(render_lazy_report(results), encoding="utf-8", newline="\n")
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"severity={severity}")
    print(f"wrote: {args.report}")
    print(f"wrote: {args.lazy_report}")
    print(f"wrote: {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
