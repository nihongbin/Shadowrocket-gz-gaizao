#!/usr/bin/env python3
"""Create or update the S1.1 rule-source registry.

The registry is the baseline used by GitHub Actions monitoring. It records the
remote URLs that S1.1 depends on or watches, plus the expected content hash for
rule sources. DoH endpoints are checked for reachability but do not use a hash.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse, urldefrag


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "S1-1-scenario-cn-us-lazy-stabilized-v0.conf"
DEFAULT_JSON = ROOT / "references" / "rule-source-registry.json"
DEFAULT_MD = ROOT / "references" / "rule-source-registry.md"
LAZY_URL = "https://johnshall.github.io/Shadowrocket-ADBlock-Rules-Forever/lazy.conf"
URL_PATTERN = re.compile(r"https?://[^\s,]+")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def fetch_bytes(url: str) -> bytes:
    fetch_url, _ = urldefrag(url)
    req = urllib.request.Request(fetch_url, headers={"User-Agent": "s1-1-source-sync/1.0"})
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read()
        except Exception as exc:  # noqa: BLE001 - network errors are intentionally retried here.
            last_error = exc
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"failed to fetch {url}: {last_error}") from last_error


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def extract_urls(config_text: str) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for match in URL_PATTERN.findall(config_text):
        cleaned = match.rstrip(").,")
        if cleaned not in seen:
            seen.add(cleaned)
            urls.append(cleaned)
    if LAZY_URL not in seen:
        urls.insert(0, LAZY_URL)
    return urls


def source_id_for_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.strip("/")
    if host == "johnshall.github.io":
        return "johnshall-lazy"
    if "cloudflare-dns.com" in host:
        if "security" in host:
            return "doh-cloudflare-security"
        return "doh-cloudflare"
    if host == "dns.google":
        return "doh-google"
    if host == "raw.githubusercontent.com":
        parts = path.split("/")
        if len(parts) >= 6 and parts[0].lower() == "blackmatrix7":
            family = parts[-2].lower()
            return f"blackmatrix7-{family}"
    safe = re.sub(r"[^a-z0-9]+", "-", f"{host}-{path}".lower()).strip("-")
    return safe[:80]


def kind_for_url(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "dns.google" in host or "cloudflare-dns.com" in host:
        return "doh"
    if "johnshall.github.io" in host:
        return "reference-upstream"
    return "runtime-rule-set"


def role_for_url(url: str) -> str:
    if "johnshall.github.io" in url:
        return "lazy reference and diff source"
    if "dns.google" in url or "cloudflare-dns.com" in url:
        return "DoH resolver"
    parsed = urlparse(url)
    parts = parsed.path.strip("/").split("/")
    if len(parts) >= 2:
        return parts[-2]
    return "remote rule source"


def runtime_dependency_for_kind(kind: str) -> str:
    if kind == "runtime-rule-set":
        return "runtime"
    if kind == "doh":
        return "runtime-dns"
    return "reference-only"


def existing_entries(path: Path) -> dict[str, dict[str, object]]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(item["id"]): item for item in data.get("sources", [])}


def build_entries(urls: list[str], existing: dict[str, dict[str, object]], update_id: str | None) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for url in urls:
        sid = source_id_for_url(url)
        kind = kind_for_url(url)
        old = existing.get(sid, {})
        should_hash = kind in {"runtime-rule-set", "reference-upstream"}
        expected_sha = old.get("expected_sha256")
        status = "not-fetched"
        size = old.get("last_known_size")

        should_update = update_id in {sid, "ALL"} or expected_sha is None
        if should_hash and should_update:
            content = fetch_bytes(url)
            expected_sha = sha256_bytes(content)
            size = len(content)
            status = "baseline-updated"
        elif should_hash:
            status = "baseline-kept"

        entry = {
            "id": sid,
            "url": url,
            "kind": kind,
            "role": old.get("role") or role_for_url(url),
            "runtime_dependency": old.get("runtime_dependency") or runtime_dependency_for_kind(kind),
            "expected_sha256": expected_sha,
            "last_known_size": size,
            "license_note": old.get("license_note") or license_note_for_url(url),
            "risk_note": old.get("risk_note") or risk_note_for_kind(kind),
            "monitoring": old.get("monitoring") or monitoring_for_kind(kind),
            "baseline_status": status,
        }
        entries.append(entry)
    return sorted(entries, key=lambda item: str(item["id"]))


def license_note_for_url(url: str) -> str:
    if "johnshall" in url.lower():
        return "CC BY-SA 4.0 upstream; keep attribution when sharing."
    if "blackmatrix7" in url.lower():
        return "blackmatrix7 ios_rule_script upstream; keep upstream attribution and license notes."
    return "External source; verify license before redistribution."


def risk_note_for_kind(kind: str) -> str:
    if kind == "runtime-rule-set":
        return "Runtime remote dependency; monitor reachability, hash, and unsafe markers."
    if kind == "doh":
        return "Runtime DNS dependency; monitor reachability only."
    return "Reference source only; changes require manual review before adoption."


def monitoring_for_kind(kind: str) -> str:
    if kind == "doh":
        return "reachability"
    return "reachability, sha256, unsafe markers"


def write_json(path: Path, entries: list[dict[str, object]]) -> None:
    payload = {
        "schema": 1,
        "description": "S1.1 governed source registry. Metadata is stable and has no runtime timestamp.",
        "sources": entries,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_markdown(path: Path, entries: list[dict[str, object]]) -> None:
    lines = [
        "# S1.1 Rule Source Registry",
        "",
        "This registry records every remote URL used or monitored by S1.1. Runtime private configs, nodes, subscriptions, accounts, and proxy groups must never be added here.",
        "",
        "| Source ID | Runtime | Role | URL | Expected SHA256 | Risk |",
        "|---|---|---|---|---|---|",
    ]
    for item in entries:
        sha = str(item.get("expected_sha256") or "")
        short_sha = sha[:12] if sha else "n/a"
        lines.append(
            f"| `{item['id']}` | `{item['runtime_dependency']}` | {item['role']} | {item['url']} | `{short_sha}` | {item['risk_note']} |"
        )
    lines.extend(
        [
            "",
            "## Adoption Rules",
            "",
            "- Project-owned S1.1 templates and seed lists have priority over upstream defaults.",
            "- Johnshall lazy.conf is a reference and diff source, not a direct runtime config.",
            "- blackmatrix7 Shadowrocket RULE-SET links may remain runtime dependencies while monitored.",
            "- iab0x00 is not a runtime dependency for S1.1; useful AI domains must enter the local AI seed list after manual confirmation.",
            "- Upstream changes are reported through GitHub Issues and only enter templates through a reviewed PR.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync S1.1 rule-source registry baselines.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MD)
    parser.add_argument(
        "--source-id",
        help="Only refresh one source id. Use ALL to refresh every hash. Default creates missing baselines and keeps existing ones.",
    )
    args = parser.parse_args()

    config_text = read_text(args.config)
    urls = extract_urls(config_text)
    existing = existing_entries(args.json)
    entries = build_entries(urls, existing, args.source_id)
    if args.source_id and args.source_id != "ALL" and args.source_id not in {str(item["id"]) for item in entries}:
        print(f"unknown source id: {args.source_id}", file=sys.stderr)
        return 2
    write_json(args.json, entries)
    write_markdown(args.markdown, entries)
    print(f"wrote: {args.json}")
    print(f"wrote: {args.markdown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
