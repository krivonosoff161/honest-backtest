"""File-based strategy registry and experiment queue contracts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import ExperimentQueueConfig, ExperimentQueueResult, RegistryConfig, RegistryWriteResult
from .paths import ensure_output_layout

ALLOWED_REGISTRY_STATUSES = {"draft", "tested", "rejected", "weak", "needs_forward", "research_note"}
BLOCKED_STATUS_WORDS = {"approved", "profitable", "ready", "live", "trade"}
ALLOWED_CREATED_BY = {"human", "rule", "llm"}


def initialize_registry(config: RegistryConfig) -> dict[str, Any]:
    """Create the private registry and queue layout without seeding findings."""
    out_dir = config.out_dir.resolve()
    paths = ensure_output_layout(out_dir)
    created_at = config.created_at or _utc_now()
    metadata_path = paths["registry"] / "metadata.json"
    if not metadata_path.exists():
        _write_json(
            metadata_path,
            {
                "schema_version": 1,
                "created_at": created_at,
                "purpose": "private strategy research registry",
                "allowed_statuses": sorted(ALLOWED_REGISTRY_STATUSES),
                "release_rule": "registry evidence is research-only and never implies live execution permission",
            },
        )
    return {
        "schema_version": 1,
        "created_at": created_at,
        "out_dir": str(out_dir),
        "metadata_path": str(metadata_path),
        "registry_path": str(paths["registry"] / "registry_entries.jsonl"),
        "queue_path": str(paths["experiment_queue"]),
    }


def append_registry_entry(entry_path: Path, config: RegistryConfig) -> RegistryWriteResult:
    """Validate and append a research registry entry to JSONL."""
    out_dir = config.out_dir.resolve()
    paths = ensure_output_layout(out_dir)
    created_at = config.created_at or _utc_now()
    run_id = config.run_id or _run_id(created_at)
    entry = _read_json_object(entry_path)
    normalized = _validate_registry_entry(entry, created_at, run_id)
    record_id = str(normalized["registry_id"])

    record_path = paths["registry"] / f"{record_id}.json"
    index_path = paths["registry"] / "registry_entries.jsonl"
    if record_path.exists():
        raise ValueError(f"registry record already exists: {record_id}")
    _write_json(record_path, normalized)
    _append_jsonl(index_path, normalized)
    return RegistryWriteResult(
        record_id=record_id,
        created_at=str(normalized["created_at"]),
        out_dir=out_dir,
        record_path=record_path,
        index_path=index_path,
    )


def queue_experiment_plan(plan_path: Path, config: ExperimentQueueConfig) -> ExperimentQueueResult:
    """Validate an experiment plan and write it to the append-only queue."""
    out_dir = config.out_dir.resolve()
    paths = ensure_output_layout(out_dir)
    created_at = config.created_at or _utc_now()
    run_id = config.run_id or _run_id(created_at)
    plan = _read_json_object(plan_path)
    normalized = _validate_experiment_plan(plan, config.created_by, created_at, run_id)
    experiment_id = str(normalized["experiment_id"])

    queue_path = paths["experiment_queue"] / f"{experiment_id}.json"
    index_path = paths["experiment_queue"] / "index.jsonl"
    if queue_path.exists():
        raise ValueError(f"experiment already queued: {experiment_id}")
    _write_json(queue_path, normalized)
    _append_jsonl(
        index_path,
        {
            "schema_version": 1,
            "experiment_id": experiment_id,
            "created_at": normalized["created_at"],
            "created_by": normalized["created_by"],
            "strategy_ids": normalized["strategy_ids"],
            "asset_cluster": normalized.get("asset_cluster", ""),
            "timeframes": normalized["timeframes"],
            "queue_path": str(queue_path),
        },
    )
    return ExperimentQueueResult(
        experiment_id=experiment_id,
        created_at=str(normalized["created_at"]),
        out_dir=out_dir,
        queue_path=queue_path,
        index_path=index_path,
    )


def _validate_registry_entry(entry: dict[str, Any], created_at: str, run_id: str) -> dict[str, Any]:
    normalized = dict(entry)
    normalized.setdefault("schema_version", 1)
    normalized.setdefault("registry_id", f"reg_{run_id}")
    normalized.setdefault("created_at", created_at)
    _require_schema_version(normalized)
    _require_non_empty_string(normalized, "registry_id")
    _require_non_empty_string(normalized, "strategy_id")
    _require_non_empty_string(normalized, "status")
    status = str(normalized["status"]).strip()
    if status not in ALLOWED_REGISTRY_STATUSES:
        raise ValueError(f"registry status must be one of {sorted(ALLOWED_REGISTRY_STATUSES)}")
    _reject_blocked_status_words(normalized)
    normalized["status"] = status
    normalized["filters"] = _dict_field(normalized, "filters")
    normalized["evidence_refs"] = _string_list(normalized, "evidence_refs", allow_empty=False)
    normalized["works_when"] = _string_list(normalized, "works_when", allow_empty=True)
    normalized["fails_when"] = _string_list(normalized, "fails_when", allow_empty=True)
    return normalized


def _validate_experiment_plan(
    plan: dict[str, Any],
    created_by: str,
    created_at: str,
    run_id: str,
) -> dict[str, Any]:
    if created_by not in ALLOWED_CREATED_BY:
        raise ValueError(f"created_by must be one of {sorted(ALLOWED_CREATED_BY)}")
    normalized = dict(plan)
    normalized.setdefault("schema_version", 1)
    normalized.setdefault("experiment_id", f"exp_{run_id}")
    normalized.setdefault("created_at", created_at)
    normalized.setdefault("created_by", created_by)
    normalized.setdefault("status", "queued")
    _require_schema_version(normalized)
    _require_non_empty_string(normalized, "experiment_id")
    _require_non_empty_string(normalized, "hypothesis")
    if normalized["created_by"] not in ALLOWED_CREATED_BY:
        raise ValueError(f"plan.created_by must be one of {sorted(ALLOWED_CREATED_BY)}")
    if normalized["status"] not in {"draft", "queued"}:
        raise ValueError("plan.status must be draft or queued")
    normalized["status"] = "queued"
    normalized["strategy_ids"] = _string_list(normalized, "strategy_ids", allow_empty=False)
    normalized["timeframes"] = _string_list(normalized, "timeframes", allow_empty=False)
    normalized["assets"] = _string_list(normalized, "assets", allow_empty=True)
    if not normalized["assets"] and not _non_empty_string(normalized.get("asset_cluster")):
        raise ValueError("plan must define assets or asset_cluster")
    normalized["parameter_grid"] = _dict_field(normalized, "parameter_grid")
    normalized["filters"] = _dict_field(normalized, "filters")
    normalized["data_window"] = _dict_field(normalized, "data_window")
    normalized["budgets"] = _validate_budgets(_dict_field(normalized, "budgets"))
    _reject_blocked_status_words(normalized)
    return normalized


def _validate_budgets(budgets: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(budgets)
    max_variants = _positive_int(normalized, "max_variants", maximum=10_000)
    max_runtime_seconds = _positive_int(normalized, "max_runtime_seconds", maximum=86_400)
    if int(normalized.get("max_symbols", 1)) > 250:
        raise ValueError("budgets.max_symbols must be <= 250")
    if int(normalized.get("max_timeframes", 1)) > 12:
        raise ValueError("budgets.max_timeframes must be <= 12")
    if normalized.get("llm_enabled", False) is not False:
        raise ValueError("experiment plans may not enable LLM calls inside the runner")
    normalized["max_variants"] = max_variants
    normalized["max_runtime_seconds"] = max_runtime_seconds
    normalized["llm_enabled"] = False
    return normalized


def _read_json_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def _require_schema_version(item: dict[str, Any]) -> None:
    if item.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")


def _require_non_empty_string(item: dict[str, Any], field: str) -> None:
    if not _non_empty_string(item.get(field)):
        raise ValueError(f"{field} must be a non-empty string")


def _non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(item: dict[str, Any], field: str, allow_empty: bool) -> list[str]:
    values = item.get(field, [])
    if not isinstance(values, list) or not all(_non_empty_string(value) for value in values):
        raise ValueError(f"{field} must be a list of non-empty strings")
    if not allow_empty and not values:
        raise ValueError(f"{field} must not be empty")
    return [str(value).strip() for value in values]


def _dict_field(item: dict[str, Any], field: str) -> dict[str, Any]:
    value = item.get(field, {})
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _positive_int(item: dict[str, Any], field: str, maximum: int) -> int:
    value = item.get(field)
    if not isinstance(value, int) or value < 1:
        raise ValueError(f"{field} must be a positive integer")
    if value > maximum:
        raise ValueError(f"{field} must be <= {maximum}")
    return value


def _reject_blocked_status_words(item: dict[str, Any]) -> None:
    text = json.dumps(item, ensure_ascii=False).lower()
    blocked = sorted(word for word in BLOCKED_STATUS_WORDS if word in text)
    if blocked:
        raise ValueError(f"blocked execution or profitability wording in research record: {blocked}")


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return path


def _append_jsonl(path: Path, item: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _run_id(created_at: str) -> str:
    return "".join(ch for ch in created_at if ch.isdigit())[:14]
