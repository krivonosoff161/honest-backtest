"""Read-only inventory for local Strategy Discovery Lab data sources."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional, TextIO

from .models import FileSummary, InventoryConfig, InventoryResult
from .paths import ensure_output_layout, relative_to_or_name

TICK_HEADER = ["ts_ms", "recv_ts_ms", "symbol", "side", "price", "size", "trade_id"]
FEATURE_CORE_FIELDS = {
    "schema_version",
    "ts_ms",
    "ts",
    "symbol",
    "base_symbol",
    "tf",
    "open",
    "high",
    "low",
    "close",
    "volume_contracts",
    "volume_usdt",
    "regime",
}


def run_inventory(config: InventoryConfig) -> InventoryResult:
    """Build a private manifest from configured local data roots.

    The inventory is read-only with respect to all source roots. It writes only
    below ``config.out_dir``.
    """
    source_root = config.source_root.resolve()
    tick_root = config.tick_root.resolve() if config.tick_root else None
    out_dir = config.out_dir.resolve()
    _validate_output_boundary(out_dir, source_root, tick_root)
    created_at = config.created_at or _utc_now()
    run_id = config.run_id or _run_id(created_at)
    output_paths = ensure_output_layout(out_dir)

    warnings: list[dict[str, Any]] = []
    tape_rows = _scan_tick_root(run_id, tick_root, warnings)
    feature_rows = _scan_feature_root(run_id, source_root / "logs" / "features", warnings)
    event_rows = _scan_event_logs(run_id, source_root, warnings)
    cache_rows = _scan_cache_files(run_id, source_root / "scripts", warnings)
    source_summaries = _source_summaries(source_root, tick_root)
    coverage_rows = _coverage_by_symbol(tape_rows, feature_rows)

    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "created_at": created_at,
        "source_root": str(source_root),
        "tick_root": str(tick_root) if tick_root else None,
        "out_dir": str(out_dir),
        "source_summaries": source_summaries,
        "totals": {
            "tick_files": len(tape_rows),
            "feature_files": len(feature_rows),
            "event_logs": len(event_rows),
            "cache_files": len(cache_rows),
            "quality_warnings": len(warnings),
        },
    }

    manifest_dir = output_paths["manifests"]
    report_dir = output_paths["reports"]
    manifest_path = manifest_dir / f"inventory_{run_id}.json"
    latest_path = manifest_dir / "inventory_latest.json"
    report_path = report_dir / f"inventory_{run_id}.md"

    files_written = [
        _write_json(manifest_path, manifest),
        _write_json(
            latest_path,
            {
                "schema_version": 1,
                "run_id": run_id,
                "created_at": created_at,
                "manifest_path": str(manifest_path),
                "report_path": str(report_path),
            },
        ),
        _write_csv(manifest_dir / f"tape_files_{run_id}.csv", tape_rows),
        _write_csv(manifest_dir / f"feature_files_{run_id}.csv", feature_rows),
        _write_csv(manifest_dir / f"event_logs_{run_id}.csv", event_rows),
        _write_csv(manifest_dir / f"cache_files_{run_id}.csv", cache_rows),
        _write_csv(report_dir / f"coverage_by_symbol_{run_id}.csv", coverage_rows),
        _write_csv(report_dir / f"quality_warnings_{run_id}.csv", warnings),
        _write_text(report_path, _render_summary(manifest, coverage_rows, warnings)),
    ]

    return InventoryResult(
        run_id=run_id,
        created_at=created_at,
        out_dir=out_dir,
        manifest_path=manifest_path,
        latest_path=latest_path,
        report_path=report_path,
        files_written=files_written,
    )


def _scan_tick_root(run_id: str, tick_root: Optional[Path], warnings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if tick_root is None or not tick_root.exists():
        if tick_root is not None:
            warnings.append(_warning(run_id, "tick_tape", tick_root, "missing_root", "tick root does not exist"))
        return []

    rows: list[dict[str, Any]] = []
    for path in sorted(_iter_files(tick_root, {".csv", ".gz"})):
        summary = _file_summary(run_id, "tick_tape", tick_root, path)
        row = summary.to_dict()
        symbol = path.parent.name
        date_utc = _date_from_stem(path)
        row.update(
            {
                "symbol": symbol,
                "date_utc": date_utc,
                "format": "csv_gz" if path.suffix.lower() == ".gz" else "csv",
                "row_count": 0,
                "first_ts_ms": "",
                "last_ts_ms": "",
                "first_recv_ts_ms": "",
                "last_recv_ts_ms": "",
                "side_values": "",
                "gap_marker_count": 0,
                "min_price": "",
                "max_price": "",
                "total_size": "",
                "duplicate_trade_id_count": 0,
                "header_ok": False,
            }
        )
        try:
            stats = _scan_tick_file(path)
            row.update(stats)
            row["schema_header"] = ",".join(stats["header"])
            row["schema_hash"] = _schema_hash(stats["header"])
            if not stats["header_ok"]:
                warnings.append(_warning(run_id, "tick_tape", path, "bad_header", row["schema_header"]))
        except Exception as exc:  # pragma: no cover - defensive for local corrupt files
            row.update({"readable": False, "error": str(exc)})
            warnings.append(_warning(run_id, "tick_tape", path, "read_error", str(exc)))
        rows.append(row)
    return rows


def _scan_tick_file(path: Path) -> dict[str, Any]:
    with _open_text(path) as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        seen_trade_ids: set[str] = set()
        duplicate_trade_ids = 0
        side_values: set[str] = set()
        row_count = 0
        gap_marker_count = 0
        first_ts = last_ts = first_recv = last_recv = ""
        min_price: float | None = None
        max_price: float | None = None
        total_size = 0.0
        for item in reader:
            row_count += 1
            ts_ms = item.get("ts_ms") or ""
            recv_ts_ms = item.get("recv_ts_ms") or ""
            if row_count == 1:
                first_ts = ts_ms
                first_recv = recv_ts_ms
            last_ts = ts_ms
            last_recv = recv_ts_ms
            side = item.get("side") or ""
            if side:
                side_values.add(side)
            if side == "GAP":
                gap_marker_count += 1
            trade_id = item.get("trade_id") or ""
            if trade_id:
                if trade_id in seen_trade_ids:
                    duplicate_trade_ids += 1
                else:
                    seen_trade_ids.add(trade_id)
            try:
                price = float(item.get("price") or "")
                min_price = price if min_price is None else min(min_price, price)
                max_price = price if max_price is None else max(max_price, price)
            except ValueError:
                pass
            try:
                total_size += float(item.get("size") or 0.0)
            except ValueError:
                pass
    return {
        "header": header,
        "header_ok": header == TICK_HEADER,
        "row_count": row_count,
        "first_ts_ms": first_ts,
        "last_ts_ms": last_ts,
        "first_recv_ts_ms": first_recv,
        "last_recv_ts_ms": last_recv,
        "side_values": "|".join(sorted(side_values)),
        "gap_marker_count": gap_marker_count,
        "min_price": "" if min_price is None else min_price,
        "max_price": "" if max_price is None else max_price,
        "total_size": round(total_size, 12),
        "duplicate_trade_id_count": duplicate_trade_ids,
    }


def _scan_feature_root(run_id: str, feature_root: Path, warnings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not feature_root.exists():
        warnings.append(_warning(run_id, "feature_logs", feature_root, "missing_root", "feature root does not exist"))
        return []
    index = _load_feature_index(feature_root / "_index.jsonl")
    rows: list[dict[str, Any]] = []
    for path in sorted(_iter_files(feature_root, {".csv", ".gz"})):
        if path.name == "_index.jsonl":
            continue
        summary = _file_summary(run_id, "feature_logs", feature_root, path)
        row = summary.to_dict()
        tf = path.parent.parent.name if path.parent.parent != feature_root.parent else ""
        symbol = path.parent.name
        date_utc = _date_from_stem(path)
        row.update(
            {
                "tf": tf,
                "symbol": symbol,
                "date_utc": date_utc,
                "row_count": 0,
                "start_ts_ms": "",
                "end_ts_ms": "",
                "indexed": False,
                "index_rows": "",
                "schema_version": "",
                "field_count": 0,
                "missing_required_fields": "",
            }
        )
        try:
            stats = _scan_feature_file(path)
            row.update(stats)
            rel = relative_to_or_name(path, feature_root.parent.parent)
            if rel in index:
                row.update({"indexed": True, "index_rows": index[rel].get("rows", "")})
            row["schema_header"] = ",".join(stats["header"])
            row["schema_hash"] = _schema_hash(stats["header"])
            if stats["missing_required_fields"]:
                warnings.append(
                    _warning(run_id, "feature_logs", path, "missing_required_fields", stats["missing_required_fields"])
                )
        except Exception as exc:  # pragma: no cover - defensive for local corrupt files
            row.update({"readable": False, "error": str(exc)})
            warnings.append(_warning(run_id, "feature_logs", path, "read_error", str(exc)))
        rows.append(row)
    return rows


def _scan_feature_file(path: Path) -> dict[str, Any]:
    with _open_text(path) as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        row_count = 0
        start_ts = end_ts = ""
        schema_version = ""
        for item in reader:
            row_count += 1
            ts_ms = item.get("ts_ms") or ""
            if row_count == 1:
                start_ts = ts_ms
                schema_version = item.get("schema_version") or ""
            end_ts = ts_ms
    missing = sorted(FEATURE_CORE_FIELDS - set(header))
    return {
        "header": header,
        "row_count": row_count,
        "start_ts_ms": start_ts,
        "end_ts_ms": end_ts,
        "schema_version": schema_version,
        "field_count": len(header),
        "missing_required_fields": "|".join(missing),
    }


def _scan_event_logs(run_id: str, source_root: Path, warnings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    roots = [
        ("main_signals", source_root / "logs" / "signals"),
        ("scout_journals", source_root / "logs" / "scout"),
        ("logs_archive", source_root / "logs_archive"),
        ("old_backtest_outputs", source_root / "scripts" / "backtest" / "backtest_runs"),
        ("research_reports", source_root / "scripts" / "analysis" / "research"),
    ]
    rows: list[dict[str, Any]] = []
    for dataset, root in roots:
        if not root.exists():
            warnings.append(_warning(run_id, dataset, root, "missing_root", "root does not exist"))
            continue
        for path in sorted(_iter_files(root, {".jsonl", ".json", ".csv", ".md", ".txt"})):
            if _is_noise_path(path):
                continue
            summary = _file_summary(run_id, dataset, root, path)
            row = summary.to_dict()
            row.update(
                {
                    "record_count": 0,
                    "schema_versions": "",
                    "min_ts": "",
                    "max_ts": "",
                    "id_field": "",
                    "unique_id_count": "",
                    "source_counts": "",
                    "symbol_or_asset_count": "",
                    "top_level_keys": "",
                    "json_error_count": "",
                }
            )
            try:
                if path.suffix.lower() == ".jsonl":
                    row.update(_scan_jsonl_file(path))
                elif path.suffix.lower() == ".csv":
                    row.update(_scan_csv_event_file(path))
                else:
                    row.update({"record_count": 1})
            except Exception as exc:  # pragma: no cover - defensive for local corrupt files
                row.update({"readable": False, "error": str(exc)})
                warnings.append(_warning(run_id, dataset, path, "read_error", str(exc)))
            if row.get("json_error_count") not in ("", 0):
                warnings.append(_warning(run_id, dataset, path, "json_parse_errors", str(row["json_error_count"])))
            rows.append(row)
    return rows


def _scan_jsonl_file(path: Path) -> dict[str, Any]:
    record_count = 0
    json_errors = 0
    schema_versions: set[str] = set()
    keys: set[str] = set()
    source_counts: Counter[str] = Counter()
    symbols: set[str] = set()
    ids: set[str] = set()
    id_field = ""
    min_ts = max_ts = ""
    with _open_text(path) as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                item = json.loads(stripped)
            except json.JSONDecodeError:
                json_errors += 1
                continue
            if not isinstance(item, dict):
                continue
            record_count += 1
            keys.update(str(key) for key in item.keys())
            if "schema_version" in item:
                schema_versions.add(str(item["schema_version"]))
            for candidate in ("id", "card_id", "signal_id", "event_id", "watch_id"):
                if candidate in item:
                    id_field = id_field or candidate
                    ids.add(str(item[candidate]))
                    break
            source = item.get("source") or item.get("source_id") or item.get("source_class")
            if source:
                source_counts[str(source)] += 1
            symbol = _extract_symbol(item)
            if symbol:
                symbols.add(str(symbol))
            ts = _extract_ts(item)
            if ts:
                min_ts = ts if not min_ts else min(min_ts, ts)
                max_ts = ts if not max_ts else max(max_ts, ts)
    return {
        "record_count": record_count,
        "schema_versions": "|".join(sorted(schema_versions)),
        "min_ts": min_ts,
        "max_ts": max_ts,
        "id_field": id_field,
        "unique_id_count": len(ids) if id_field else "",
        "source_counts": _compact_counter(source_counts),
        "symbol_or_asset_count": len(symbols),
        "top_level_keys": "|".join(sorted(keys)),
        "json_error_count": json_errors,
    }


def _extract_symbol(item: dict[str, Any]) -> object:
    for field in ("symbol", "asset", "instrument", "instrument_id", "inst_id", "market"):
        value = item.get(field)
        if value:
            return value
    return None


def _scan_csv_event_file(path: Path) -> dict[str, Any]:
    with _open_text(path) as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        count = sum(1 for _ in reader)
    return {
        "record_count": count,
        "schema_header": ",".join(header),
        "schema_hash": _schema_hash(header),
        "top_level_keys": "|".join(header),
    }


def _scan_cache_files(run_id: str, scripts_root: Path, warnings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not scripts_root.exists():
        warnings.append(_warning(run_id, "cache_files", scripts_root, "missing_root", "scripts root does not exist"))
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(scripts_root.rglob("*cache*")):
        if path.is_file() and path.suffix.lower() in {".pkl", ".pickle", ".json"}:
            row = _file_summary(run_id, "cache_files", scripts_root, path).to_dict()
            row.update({"cache_kind": _infer_cache_kind(path), "inferred_days": _infer_days(path)})
            rows.append(row)
    return rows


def _source_summaries(source_root: Path, tick_root: Optional[Path]) -> list[dict[str, Any]]:
    roots = [
        ("tick_tape", tick_root),
        ("feature_logs", source_root / "logs" / "features"),
        ("main_signals", source_root / "logs" / "signals"),
        ("scout_journals", source_root / "logs" / "scout"),
        ("logs_archive", source_root / "logs_archive"),
        ("old_backtest_outputs", source_root / "scripts" / "backtest" / "backtest_runs"),
        ("research_reports", source_root / "scripts" / "analysis" / "research"),
    ]
    summaries = []
    for dataset, root in roots:
        if root is None or not root.exists():
            summaries.append({"dataset": dataset, "path": str(root) if root else "", "exists": False, "file_count": 0, "byte_count": 0})
            continue
        files = [path for path in root.rglob("*") if path.is_file() and not _is_noise_path(path)]
        summaries.append(
            {
                "dataset": dataset,
                "path": str(root),
                "exists": True,
                "file_count": len(files),
                "byte_count": sum(path.stat().st_size for path in files),
            }
        )
    return summaries


def _coverage_by_symbol(tape_rows: list[dict[str, Any]], feature_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    coverage: dict[str, dict[str, Any]] = defaultdict(lambda: {"symbol": ""})
    for row in tape_rows:
        symbol = row.get("symbol") or ""
        if not symbol:
            continue
        current = coverage[symbol]
        current["symbol"] = symbol
        current["tick_file_count"] = int(current.get("tick_file_count") or 0) + 1
        _update_date_range(current, "tick", str(row.get("date_utc") or ""))
    for row in feature_rows:
        symbol = row.get("symbol") or ""
        if not symbol:
            continue
        current = coverage[symbol]
        current["symbol"] = symbol
        current["feature_file_count"] = int(current.get("feature_file_count") or 0) + 1
        tf = row.get("tf") or ""
        if tf:
            tfs = set(str(current.get("feature_timeframes") or "").split("|")) - {""}
            tfs.add(str(tf))
            current["feature_timeframes"] = "|".join(sorted(tfs))
        _update_date_range(current, "feature", str(row.get("date_utc") or ""))
    return [coverage[key] for key in sorted(coverage)]


def _update_date_range(row: dict[str, Any], prefix: str, date_utc: str) -> None:
    if not date_utc:
        return
    first_key = f"{prefix}_first_date"
    last_key = f"{prefix}_last_date"
    row[first_key] = date_utc if not row.get(first_key) else min(str(row[first_key]), date_utc)
    row[last_key] = date_utc if not row.get(last_key) else max(str(row[last_key]), date_utc)


def _render_summary(manifest: dict[str, Any], coverage_rows: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> str:
    totals = manifest["totals"]
    lines = [
        "# Strategy Lab Inventory",
        "",
        f"- Run: `{manifest['run_id']}`",
        f"- Created: `{manifest['created_at']}`",
        f"- Tick files: {totals['tick_files']}",
        f"- Feature files: {totals['feature_files']}",
        f"- Event logs: {totals['event_logs']}",
        f"- Cache files: {totals['cache_files']}",
        f"- Quality warnings: {totals['quality_warnings']}",
        "",
        "## Source Summary",
        "",
        "| Dataset | Exists | Files | Bytes |",
        "|---|---:|---:|---:|",
    ]
    for item in manifest["source_summaries"]:
        lines.append(f"| {item['dataset']} | {item['exists']} | {item['file_count']} | {item['byte_count']} |")
    lines.extend(["", "## Coverage", ""])
    if coverage_rows:
        lines.extend(["| Symbol | Tick files | Tick range | Feature files | Feature TFs | Feature range |", "|---|---:|---|---:|---|---|"])
        for row in coverage_rows[:25]:
            tick_range = _range_text(row.get("tick_first_date"), row.get("tick_last_date"))
            feature_range = _range_text(row.get("feature_first_date"), row.get("feature_last_date"))
            lines.append(
                "| {symbol} | {ticks} | {tick_range} | {features} | {tfs} | {feature_range} |".format(
                    symbol=row.get("symbol", ""),
                    ticks=row.get("tick_file_count", 0),
                    tick_range=tick_range,
                    features=row.get("feature_file_count", 0),
                    tfs=row.get("feature_timeframes", ""),
                    feature_range=feature_range,
                )
            )
        if len(coverage_rows) > 25:
            lines.append(f"| ... | ... | ... | ... | ... | {len(coverage_rows) - 25} more symbols |")
    else:
        lines.append("No symbol coverage detected.")
    lines.extend(["", "## Warnings", ""])
    if warnings:
        lines.extend(["| Dataset | Path | Code | Detail |", "|---|---|---|---|"])
        for item in warnings[:50]:
            lines.append(f"| {item['dataset']} | `{item['path']}` | {item['code']} | {item['detail']} |")
    else:
        lines.append("No quality warnings.")
    lines.append("")
    return "\n".join(lines)


def _file_summary(run_id: str, dataset: str, root: Path, path: Path) -> FileSummary:
    stat = path.stat()
    return FileSummary(
        run_id=run_id,
        dataset=dataset,
        root=str(root),
        rel_path=relative_to_or_name(path, root),
        abs_path=str(path),
        file_name=path.name,
        ext=path.suffix.lower(),
        compression="gzip" if path.suffix.lower() == ".gz" else "",
        size_bytes=stat.st_size,
        mtime_utc=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def _validate_output_boundary(out_dir: Path, source_root: Path, tick_root: Optional[Path]) -> None:
    if _is_relative_to(out_dir, source_root):
        raise ValueError("out_dir must not be inside source_root")
    if tick_root is not None and _is_relative_to(out_dir, tick_root):
        raise ValueError("out_dir must not be inside tick_root")


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _iter_files(root: Path, suffixes: set[str]) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in suffixes and not _is_noise_path(path):
            yield path


def _is_noise_path(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    if {".git", ".pytest_cache", ".ruff_cache", "__pycache__", "charts"} & parts:
        return True
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".pyc"}:
        return True
    return False


def _open_text(path: Path) -> TextIO:
    if path.suffix.lower() == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", newline="")
    return path.open("r", encoding="utf-8", newline="")


def _load_feature_index(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    index: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            rel = item.get("path")
            if rel:
                index[str(rel)] = item
    return index


def _date_from_stem(path: Path) -> str:
    stem = path.stem
    if path.suffix.lower() == ".gz":
        stem = Path(stem).stem
    return stem


def _schema_hash(header: list[str]) -> str:
    return hashlib.sha256(",".join(header).encode("utf-8")).hexdigest()[:16] if header else ""


def _extract_ts(item: dict[str, Any]) -> str:
    for key in ("ts_utc", "ts", "created_at", "source_ts", "outcome_ts", "labeled_at"):
        value = item.get(key)
        if value:
            return str(value)
    return ""


def _compact_counter(counter: Counter[str], limit: int = 8) -> str:
    return "|".join(f"{key}:{value}" for key, value in counter.most_common(limit))


def _infer_cache_kind(path: Path) -> str:
    name = path.name.lower()
    if "candle" in name:
        return "candles"
    if "mark" in name or "index" in name:
        return "mark_index"
    if "pump" in str(path).lower():
        return "pump"
    return "unknown"


def _infer_days(path: Path) -> str:
    for token in path.stem.replace("-", "_").split("_"):
        if token.endswith("d") and token[:-1].isdigit():
            return token[:-1]
    return ""


def _range_text(first: Any, last: Any) -> str:
    if first and last:
        return f"{first}..{last}"
    return ""


def _warning(run_id: str, dataset: str, path: Path, code: str, detail: str) -> dict[str, Any]:
    return {"run_id": run_id, "dataset": dataset, "path": str(path), "code": code, "detail": detail}


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = _fieldnames(rows)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


def _write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def _fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    for row in rows:
        for key in row:
            if key not in names:
                names.append(key)
    return names or ["empty"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id(created_at: str) -> str:
    return created_at.replace("-", "").replace(":", "").replace("T", "_").replace("Z", "")
