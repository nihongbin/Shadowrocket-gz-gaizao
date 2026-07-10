#!/usr/bin/env python3
"""Shared governance logic for V5 remote RULE-SET snapshots."""

from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable


REPOSITORY = "nihongbin/Shadowrocket-gz-gaizao"
RAW_BASE = f"https://raw.githubusercontent.com/{REPOSITORY}/main/rulesets/v5"
UPSTREAM_PREFIX = (
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/"
    "rule/Shadowrocket/"
)
UPSTREAM_LICENSE_URL = (
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/LICENSE"
)
REGISTRY_RELATIVE_PATH = Path("references/v5-mvp/ruleset-sources.json")
SNAPSHOT_DIRECTORY = Path("rulesets/v5")
LICENSE_RELATIVE_PATH = SNAPSHOT_DIRECTORY / "LICENSE.blackmatrix7-GPL-2.0.txt"
VALID_POLICIES = {"DIRECT", "PROXY"}
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
HASH_PATTERN = re.compile(r"^[A-F0-9]{64}$")
RULE_TYPE_PATTERN = re.compile(r"^[A-Z][A-Z0-9-]*$")
MAX_SOURCE_BYTES = 5 * 1024 * 1024


def _normalize_rule(raw: str) -> str | None:
    line = raw.strip().lstrip("\ufeff")
    if not line or line.startswith("#") or line.startswith("//"):
        return None
    if "<html" in line.lower() or "<!doctype" in line.lower():
        raise ValueError("upstream response looks like HTML, not a rule list")
    parts = [part.strip() for part in line.split(",")]
    if len(parts) < 2 or not RULE_TYPE_PATTERN.fullmatch(parts[0]):
        raise ValueError(f"invalid ruleset line: {line}")
    if any(not part for part in parts):
        raise ValueError(f"empty ruleset field: {line}")
    return ",".join(parts)


def canonical_rules(text: str) -> list[str]:
    """Return stable effective rules, ignoring comments, order, and duplicates."""

    rules: set[str] = set()
    for raw in text.splitlines():
        normalized = _normalize_rule(raw)
        if normalized:
            rules.add(normalized)
    if not rules:
        raise ValueError("ruleset contains no effective rules")
    # 语义比较只看有效规则集合，避免上游时间戳、注释或重排造成无意义通知。
    return sorted(rules)


def canonical_rule_text(text: str) -> str:
    return "\n".join(canonical_rules(text)) + "\n"


def semantic_sha256(text: str) -> str:
    return hashlib.sha256(canonical_rule_text(text).encode("utf-8")).hexdigest().upper()


def diff_rule_text(before: str, after: str) -> dict[str, list[str]]:
    before_rules = set(canonical_rules(before))
    after_rules = set(canonical_rules(after))
    return {
        "added": sorted(after_rules - before_rules),
        "removed": sorted(before_rules - after_rules),
    }


def governed_public_url(source_id: str) -> str:
    if not ID_PATTERN.fullmatch(source_id):
        raise ValueError(f"invalid source id: {source_id}")
    return f"{RAW_BASE}/{source_id}.list"


def render_snapshot(entry: dict[str, Any], upstream_text: str) -> str:
    rules = canonical_rules(upstream_text)
    semantic_hash = semantic_sha256(upstream_text)
    lines = [
        f"# V5 governed RULE-SET snapshot: {entry['name']}",
        f"# Upstream: {entry['upstream_url']}",
        f"# Semantic-SHA256: {semantic_hash}",
        f"# Rule-Count: {len(rules)}",
        "# Derived from blackmatrix7/ios_rule_script under GPL-2.0.",
        "# License: LICENSE.blackmatrix7-GPL-2.0.txt",
        "# No runtime timestamp is stored; comments, order, and duplicates are normalized.",
        "",
        *rules,
    ]
    return "\n".join(lines).rstrip() + "\n"


def render_registry(registry: dict[str, Any]) -> str:
    return json.dumps(registry, ensure_ascii=False, indent=2) + "\n"


def _validate_entry(entry: dict[str, Any], seen: set[str]) -> None:
    required = {
        "id",
        "name",
        "policy",
        "upstream_url",
        "snapshot_path",
        "public_url",
        "semantic_sha256",
        "rule_count",
        "license",
    }
    missing = sorted(required - set(entry))
    if missing:
        raise ValueError(f"ruleset entry missing fields: {missing}")
    source_id = entry["id"]
    if not isinstance(source_id, str) or not ID_PATTERN.fullmatch(source_id):
        raise ValueError(f"invalid ruleset id: {source_id!r}")
    if source_id in seen:
        raise ValueError(f"duplicate ruleset id: {source_id}")
    seen.add(source_id)
    if entry["policy"] not in VALID_POLICIES:
        raise ValueError(f"invalid policy for {source_id}: {entry['policy']}")
    if not str(entry["upstream_url"]).startswith(UPSTREAM_PREFIX):
        raise ValueError(f"unexpected upstream URL for {source_id}")
    expected_snapshot = (SNAPSHOT_DIRECTORY / f"{source_id}.list").as_posix()
    if entry["snapshot_path"] != expected_snapshot:
        raise ValueError(f"unexpected snapshot path for {source_id}")
    if entry["public_url"] != governed_public_url(source_id):
        raise ValueError(f"unexpected public URL for {source_id}")
    if not HASH_PATTERN.fullmatch(str(entry["semantic_sha256"])):
        raise ValueError(f"invalid semantic hash for {source_id}")
    if not isinstance(entry["rule_count"], int) or entry["rule_count"] <= 0:
        raise ValueError(f"invalid rule count for {source_id}")
    if entry["license"] != "GPL-2.0":
        raise ValueError(f"unexpected license for {source_id}")


def validate_registry(registry: dict[str, Any]) -> None:
    if registry.get("schema_version") != 1:
        raise ValueError("unsupported ruleset registry schema")
    if registry.get("repository") != REPOSITORY:
        raise ValueError("ruleset registry repository mismatch")
    sources = registry.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("ruleset registry has no sources")
    seen: set[str] = set()
    for entry in sources:
        if not isinstance(entry, dict):
            raise ValueError("ruleset registry source must be an object")
        _validate_entry(entry, seen)


def load_registry(path: Path, root: Path | None = None) -> dict[str, Any]:
    registry = json.loads(path.read_text(encoding="utf-8"))
    validate_registry(registry)
    if root is not None:
        root_resolved = root.resolve()
        for entry in registry["sources"]:
            snapshot = (root / entry["snapshot_path"]).resolve()
            try:
                snapshot.relative_to(root_resolved)
            except ValueError as exc:
                raise ValueError(f"snapshot escapes project root: {snapshot}") from exc
    return registry


def validate_snapshots(root: Path, registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for entry in registry["sources"]:
        snapshot_path = root / entry["snapshot_path"]
        if not snapshot_path.exists():
            errors.append(f"missing snapshot: {entry['id']}")
            continue
        try:
            text = snapshot_path.read_text(encoding="utf-8-sig")
            rules = canonical_rules(text)
            actual_hash = semantic_sha256(text)
            if actual_hash != entry["semantic_sha256"]:
                errors.append(f"semantic hash mismatch: {entry['id']}")
            if len(rules) != entry["rule_count"]:
                errors.append(f"rule count mismatch: {entry['id']}")
            if text != render_snapshot(entry, text):
                errors.append(f"snapshot rendering drift: {entry['id']}")
        except Exception as exc:  # noqa: BLE001 - surface every malformed tracked snapshot.
            errors.append(f"invalid snapshot {entry['id']}: {exc}")
    license_path = root / LICENSE_RELATIVE_PATH
    if not license_path.exists():
        errors.append(f"missing upstream license: {LICENSE_RELATIVE_PATH.as_posix()}")
    elif "GNU GENERAL PUBLIC LICENSE" not in license_path.read_text(
        encoding="utf-8-sig"
    ):
        errors.append("blackmatrix7 license copy is invalid")
    return errors


def analyze_source(
    entry: dict[str, Any], upstream_text: str, snapshot_text: str
) -> dict[str, Any]:
    upstream_rules = canonical_rules(upstream_text)
    snapshot_rules = canonical_rules(snapshot_text)
    upstream_hash = semantic_sha256(upstream_text)
    snapshot_hash = semantic_sha256(snapshot_text)
    base = {
        "id": entry["id"],
        "name": entry["name"],
        "policy": entry["policy"],
        "upstream_url": entry["upstream_url"],
        "expected_semantic_sha256": entry["semantic_sha256"],
        "upstream_semantic_sha256": upstream_hash,
        "snapshot_semantic_sha256": snapshot_hash,
        "upstream_rule_count": len(upstream_rules),
        "snapshot_rule_count": len(snapshot_rules),
    }
    if (
        snapshot_hash != entry["semantic_sha256"]
        or len(snapshot_rules) != entry["rule_count"]
    ):
        return {**base, "status": "SNAPSHOT_DRIFT", "added": [], "removed": []}
    if upstream_hash != entry["semantic_sha256"]:
        changes = diff_rule_text(snapshot_text, upstream_text)
        return {**base, "status": "CHANGED", **changes}
    return {**base, "status": "OK", "added": [], "removed": []}


def sync_registry_sources(
    root: Path,
    registry: dict[str, Any],
    source_text_by_id: dict[str, str],
) -> list[str]:
    changed: list[str] = []
    for entry in registry["sources"]:
        source_id = entry["id"]
        if source_id not in source_text_by_id:
            raise ValueError(f"missing fetched source: {source_id}")
        source_text = source_text_by_id[source_id]
        rules = canonical_rules(source_text)
        new_hash = semantic_sha256(source_text)
        snapshot_path = root / entry["snapshot_path"]
        old_text = snapshot_path.read_text(encoding="utf-8") if snapshot_path.exists() else None
        metadata_changed = (
            entry.get("semantic_sha256") != new_hash
            or entry.get("rule_count") != len(rules)
            or entry.get("license") != "GPL-2.0"
        )
        entry["semantic_sha256"] = new_hash
        entry["rule_count"] = len(rules)
        entry["license"] = "GPL-2.0"
        desired = render_snapshot(entry, source_text)
        if metadata_changed or old_text != desired:
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            snapshot_path.write_text(desired, encoding="utf-8", newline="\n")
            changed.append(source_id)
    return changed


def fetch_url(url: str, timeout: int = 45) -> str:
    if not url.startswith("https://"):
        raise ValueError(f"only HTTPS sources are allowed: {url}")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": f"{REPOSITORY} V5 ruleset monitor"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_SOURCE_BYTES:
            raise ValueError(f"source exceeds {MAX_SOURCE_BYTES} bytes: {url}")
        payload = response.read(MAX_SOURCE_BYTES + 1)
        if len(payload) > MAX_SOURCE_BYTES:
            raise ValueError(f"source exceeds {MAX_SOURCE_BYTES} bytes: {url}")
        return payload.decode("utf-8-sig")


def fetch_registry_sources(
    registry: dict[str, Any],
    fetcher: Callable[[str], str] = fetch_url,
    attempts: int = 3,
    retry_delay_seconds: float = 1.0,
) -> tuple[dict[str, str], dict[str, str]]:
    if attempts < 1:
        raise ValueError("fetch attempts must be at least 1")

    def fetch_with_retry(url: str) -> str:
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                return fetcher(url)
            except Exception as exc:  # noqa: BLE001 - retry transport and validation failures.
                last_error = exc
                if attempt + 1 < attempts and retry_delay_seconds > 0:
                    time.sleep(retry_delay_seconds * (2**attempt))
        assert last_error is not None
        raise last_error

    contents: dict[str, str] = {}
    errors: dict[str, str] = {}
    workers = min(8, len(registry["sources"]))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(fetch_with_retry, entry["upstream_url"]): entry
            for entry in registry["sources"]
        }
        for future in as_completed(futures):
            entry = futures[future]
            try:
                text = future.result()
                canonical_rules(text)
                contents[entry["id"]] = text
            except Exception as exc:  # noqa: BLE001 - every upstream failure is reported.
                errors[entry["id"]] = str(exc)
    return contents, errors


def source_id_from_name(name: str) -> str:
    source_id = name.rsplit("/", 1)[-1].lower()
    source_id = re.sub(r"[^a-z0-9]+", "-", source_id).strip("-")
    if not source_id:
        raise ValueError(f"cannot derive source id from {name!r}")
    return source_id


def read_legacy_ruleset_rows(path: Path) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split(",", 2)]
        if len(parts) != 3:
            raise ValueError(f"malformed remote ruleset row: {line}")
        policy, name, url = parts
        if policy not in VALID_POLICIES or not url.startswith(UPSTREAM_PREFIX):
            raise ValueError(f"legacy row is not a blackmatrix7 upstream source: {line}")
        rows.append((policy, name, url))
    return rows


def registry_from_legacy_rows(rows: list[tuple[str, str, str]]) -> dict[str, Any]:
    sources: list[dict[str, Any]] = []
    seen: set[str] = set()
    for policy, name, upstream_url in rows:
        source_id = source_id_from_name(name)
        if source_id in seen:
            raise ValueError(f"duplicate derived source id: {source_id}")
        seen.add(source_id)
        sources.append(
            {
                "id": source_id,
                "name": name,
                "policy": policy,
                "upstream_url": upstream_url,
                "snapshot_path": (SNAPSHOT_DIRECTORY / f"{source_id}.list").as_posix(),
                "public_url": governed_public_url(source_id),
                "semantic_sha256": "0" * 64,
                "rule_count": 1,
                "license": "GPL-2.0",
            }
        )
    return {
        "schema_version": 1,
        "repository": REPOSITORY,
        "sources": sources,
    }


def rewrite_rule_manifests(root: Path, registry: dict[str, Any]) -> None:
    manifest_dir = root / "references" / "v5-mvp"
    remote_path = manifest_dir / "remote-rulesets.csv"
    lazy_path = manifest_dir / "lazy-body-rules.txt"
    remote_lines = [
        "# policy,name,url",
        *[
            f"{entry['policy']},{entry['name']},{entry['public_url']}"
            for entry in registry["sources"]
        ],
    ]
    remote_path.write_text("\n".join(remote_lines) + "\n", encoding="utf-8", newline="\n")

    entries = registry["sources"]
    index = 0
    output: list[str] = []
    for raw in lazy_path.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped.startswith("RULE-SET,"):
            output.append(raw.rstrip())
            continue
        if index >= len(entries):
            raise ValueError("lazy-body-rules.txt has more RULE-SET entries than registry")
        parts = [part.strip() for part in stripped.split(",", 2)]
        entry = entries[index]
        allowed_urls = {entry["upstream_url"], entry["public_url"]}
        if len(parts) != 3 or parts[1] not in allowed_urls or parts[2] != entry["policy"]:
            raise ValueError(
                f"lazy RULE-SET order/policy mismatch at {entry['id']}: {stripped}"
            )
        output.append(f"RULE-SET,{entry['public_url']},{entry['policy']}")
        index += 1
    if index != len(entries):
        raise ValueError("lazy-body-rules.txt has fewer RULE-SET entries than registry")
    lazy_path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8", newline="\n")


def validate_rule_manifests(root: Path, registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    manifest_dir = root / "references" / "v5-mvp"
    expected_remote = [
        (entry["policy"], entry["name"], entry["public_url"])
        for entry in registry["sources"]
    ]
    actual_remote: list[tuple[str, str, str]] = []
    try:
        for raw in (manifest_dir / "remote-rulesets.csv").read_text(
            encoding="utf-8"
        ).splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = tuple(part.strip() for part in line.split(",", 2))
            if len(parts) != 3:
                raise ValueError(f"malformed row: {line}")
            actual_remote.append(parts)  # type: ignore[arg-type]
    except Exception as exc:  # noqa: BLE001
        errors.append(f"invalid remote-rulesets.csv: {exc}")
    if actual_remote != expected_remote:
        errors.append("remote-rulesets.csv differs from governed registry")

    actual_lazy: list[tuple[str, str]] = []
    lazy_text = (manifest_dir / "lazy-body-rules.txt").read_text(encoding="utf-8")
    for raw in lazy_text.splitlines():
        line = raw.strip()
        if line.startswith("RULE-SET,"):
            parts = [part.strip() for part in line.split(",", 2)]
            if len(parts) != 3:
                errors.append(f"malformed lazy RULE-SET: {line}")
                continue
            actual_lazy.append((parts[2], parts[1]))
    expected_lazy = [
        (entry["policy"], entry["public_url"]) for entry in registry["sources"]
    ]
    if actual_lazy != expected_lazy:
        errors.append("lazy-body-rules.txt differs from governed registry order")
    if "blackmatrix7/ios_rule_script/master" in lazy_text:
        errors.append("lazy-body-rules.txt still has direct upstream runtime URLs")
    return errors


def build_monitor_report(
    root: Path,
    registry: dict[str, Any],
    fetched: dict[str, str],
    fetch_errors: dict[str, str],
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for entry in registry["sources"]:
        source_id = entry["id"]
        if source_id in fetch_errors:
            results.append(
                {
                    "id": source_id,
                    "name": entry["name"],
                    "policy": entry["policy"],
                    "upstream_url": entry["upstream_url"],
                    "status": "ERROR",
                    "error": fetch_errors[source_id],
                    "added": [],
                    "removed": [],
                }
            )
            continue
        snapshot_path = root / entry["snapshot_path"]
        if not snapshot_path.exists():
            results.append(
                {
                    "id": source_id,
                    "name": entry["name"],
                    "policy": entry["policy"],
                    "upstream_url": entry["upstream_url"],
                    "status": "SNAPSHOT_DRIFT",
                    "error": "tracked snapshot is missing",
                    "added": [],
                    "removed": [],
                }
            )
            continue
        results.append(
            analyze_source(
                entry,
                fetched[source_id],
                snapshot_path.read_text(encoding="utf-8-sig"),
            )
        )
    changed = sum(item["status"] == "CHANGED" for item in results)
    errors = sum(item["status"] == "ERROR" for item in results)
    drift = sum(item["status"] == "SNAPSHOT_DRIFT" for item in results)
    status = "ERROR" if errors or drift else "CHANGED" if changed else "OK"
    return {
        "status": status,
        "changed_count": changed,
        "error_count": errors,
        "snapshot_drift_count": drift,
        "action_required": status != "OK",
        "results": results,
    }


def render_monitor_markdown(report: dict[str, Any], simulated_source_id: str = "") -> str:
    lines = [
        "# V5 规则源语义监控报告",
        "",
        f"- 状态：`{report['status']}`",
        f"- 语义变化：`{report['changed_count']}`",
        f"- 拉取异常：`{report['error_count']}`",
        f"- 本地快照漂移：`{report['snapshot_drift_count']}`",
    ]
    if simulated_source_id:
        lines.extend(
            [
                f"- 本次为通知链路模拟：`{simulated_source_id}`",
                "- 模拟结果不能批准进入正式 PR。",
            ]
        )
    lines.extend(
        [
            "",
            "上游变化不会自动修改正式配置。先审查下方差异；真实变化确认可采纳后，在本 Issue 单独一行评论：",
            "",
            "```text",
            "/approve-v5-ruleset-update",
            "```",
            "",
            "该命令只会创建 PR，不会自动合并。",
        ]
    )
    for item in report["results"]:
        if item["status"] == "OK":
            continue
        lines.extend(
            [
                "",
                f"## {item['name']} (`{item['status']}`)",
                "",
                f"- 策略：`{item['policy']}`",
                f"- 上游：{item['upstream_url']}",
            ]
        )
        if item.get("error"):
            lines.append(f"- 异常：`{item['error']}`")
        added = item.get("added", [])
        removed = item.get("removed", [])
        if added:
            lines.append(f"- 新增规则：`{len(added)}`，示例：")
            lines.extend([f"  - `{rule}`" for rule in added[:5]])
            if len(added) > 5:
                lines.append(f"  - 其余 `{len(added) - 5}` 条请在 PR 完整差异中查看。")
        if removed:
            lines.append(f"- 删除规则：`{len(removed)}`，示例：")
            lines.extend([f"  - `{rule}`" for rule in removed[:5]])
            if len(removed) > 5:
                lines.append(f"  - 其余 `{len(removed) - 5}` 条请在 PR 完整差异中查看。")
    return "\n".join(lines).rstrip() + "\n"
