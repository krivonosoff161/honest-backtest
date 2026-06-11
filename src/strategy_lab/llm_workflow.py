"""LLM planning workflow for the experimental Strategy Discovery Lab."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .llm import make_request, provider_for_name, validate_budget, validate_live_switches
from .models import LLMConfig, LLMMessage, LLMRunResult


def estimate_llm_plan(inventory_latest: Path, config: LLMConfig) -> dict[str, Any]:
    messages = build_planning_messages(inventory_latest)
    request = make_request(
        provider=config.provider,
        model=config.model,
        messages=messages,
        max_output_tokens=config.max_output_tokens,
        live=False,
    )
    validate_budget(request, config)
    return {
        "schema_version": 1,
        "mode": "estimate",
        "provider": config.provider,
        "model": config.model,
        "estimated_input_tokens": request.estimated_input_tokens,
        "estimated_output_tokens": request.estimated_output_tokens,
        "estimated_usd": request.estimated_usd,
        "run_usd_cap": config.run_usd_cap,
        "daily_usd_cap": config.daily_usd_cap,
        "max_calls": config.max_calls,
        "live_required_switches": [
            "--live",
            "--i-accept-cost",
            "STRATEGY_LAB_LLM_ENABLED=true",
            config.api_key_env,
        ],
    }


def run_llm_plan(inventory_latest: Path, config: LLMConfig) -> LLMRunResult:
    created_at = config.created_at or _utc_now()
    run_id = config.run_id or _run_id(created_at)
    run_dir = config.out_dir / "llm-runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    messages = build_planning_messages(inventory_latest)
    request = make_request(
        provider=config.provider,
        model=config.model,
        messages=messages,
        max_output_tokens=config.max_output_tokens,
        live=config.live,
    )
    validate_budget(request, config)
    validate_live_switches(config)

    request_path = run_dir / "request.json"
    request_path.write_text(json.dumps(request.to_dict(), indent=2, sort_keys=True), encoding="utf-8", newline="\n")

    provider = provider_for_name(config.provider)
    response = provider.complete(request, config)
    proposal = parse_and_validate_proposal(response.text)

    response_path = run_dir / "response.json"
    proposal_path = config.out_dir / "llm-proposals" / f"proposal_{run_id}.json"
    cost_path = config.out_dir / "llm-costs" / f"{created_at[:10]}.jsonl"
    proposal_path.parent.mkdir(parents=True, exist_ok=True)
    cost_path.parent.mkdir(parents=True, exist_ok=True)

    response_path.write_text(json.dumps(response.to_dict(), indent=2, sort_keys=True), encoding="utf-8", newline="\n")
    proposal_path.write_text(json.dumps(proposal, indent=2, sort_keys=True), encoding="utf-8", newline="\n")
    _append_jsonl(
        cost_path,
        {
            "schema_version": 1,
            "run_id": run_id,
            "created_at": created_at,
            "provider": response.provider,
            "model": response.model,
            "live": response.live,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "estimated_usd": response.estimated_usd,
        },
    )
    return LLMRunResult(
        run_id=run_id,
        created_at=created_at,
        out_dir=config.out_dir,
        request_path=request_path,
        response_path=response_path,
        proposal_path=proposal_path,
        cost_path=cost_path,
        live=response.live,
        estimated_usd=response.estimated_usd,
    )


def build_planning_messages(inventory_latest: Path) -> list[LLMMessage]:
    digest = build_inventory_digest(inventory_latest)
    system = (
        "You are a cautious research planner for a private strategy discovery lab. "
        "You do not produce trading signals, live orders, production approvals, or claims of profitability. "
        "You propose small deterministic simulation batches for later code validation."
    )
    user = (
        "Use this private inventory digest to propose the next research batch. "
        "Return strict JSON only. Do not include raw rows, private file paths, real secrets, or live-trading instructions.\n\n"
        "Required JSON shape:\n"
        "{\n"
        '  "schema_version": 1,\n'
        '  "proposal_type": "strategy_research_plan",\n'
        '  "status": "draft",\n'
        '  "hypotheses": [\n'
        "    {\n"
        '      "id": "string",\n'
        '      "asset_group": "string",\n'
        '      "strategy_family": "string",\n'
        '      "filters": ["string"],\n'
        '      "next_action": "string",\n'
        '      "safety_note": "string"\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        f"Inventory digest:\n{digest}"
    )
    return [LLMMessage("system", system), LLMMessage("user", user)]


def build_inventory_digest(inventory_latest: Path) -> str:
    latest = json.loads(inventory_latest.read_text(encoding="utf-8"))
    manifest_path = Path(str(latest["manifest_path"]))
    report_path = Path(str(latest["report_path"]))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    totals = manifest.get("totals", {})
    source_summaries = manifest.get("source_summaries", [])
    report_excerpt = _read_report_excerpt(report_path)
    sources = []
    for item in source_summaries[:12]:
        if not isinstance(item, dict):
            continue
        sources.append(
            {
                "dataset": item.get("dataset"),
                "exists": item.get("exists"),
                "files": item.get("files"),
                "bytes": item.get("bytes"),
            }
        )
    digest = {
        "run_id": latest.get("run_id"),
        "created_at": latest.get("created_at"),
        "totals": {
            "tick_files": totals.get("tick_files"),
            "feature_files": totals.get("feature_files"),
            "event_logs": totals.get("event_logs"),
            "cache_files": totals.get("cache_files"),
            "quality_warnings": totals.get("quality_warnings"),
        },
        "sources": sources,
        "report_excerpt": report_excerpt,
    }
    return json.dumps(digest, indent=2, sort_keys=True)


def parse_and_validate_proposal(text: str) -> dict[str, Any]:
    try:
        proposal = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM response is not strict JSON: {exc}") from exc
    if not isinstance(proposal, dict):
        raise ValueError("proposal must be a JSON object")
    if proposal.get("schema_version") != 1:
        raise ValueError("proposal.schema_version must be 1")
    if proposal.get("proposal_type") != "strategy_research_plan":
        raise ValueError("proposal.proposal_type must be strategy_research_plan")
    if proposal.get("status") != "draft":
        raise ValueError("proposal.status must be draft")
    hypotheses = proposal.get("hypotheses")
    if not isinstance(hypotheses, list) or not hypotheses:
        raise ValueError("proposal.hypotheses must be a non-empty list")
    for index, hypothesis in enumerate(hypotheses):
        _validate_hypothesis(index, hypothesis)
    return proposal


def _validate_hypothesis(index: int, hypothesis: object) -> None:
    if not isinstance(hypothesis, dict):
        raise ValueError(f"hypothesis {index} must be an object")
    for field in ("id", "asset_group", "strategy_family", "next_action", "safety_note"):
        if not isinstance(hypothesis.get(field), str) or not hypothesis[field].strip():
            raise ValueError(f"hypothesis {index}.{field} must be a non-empty string")
    filters = hypothesis.get("filters")
    if not isinstance(filters, list) or not filters or not all(isinstance(item, str) and item.strip() for item in filters):
        raise ValueError(f"hypothesis {index}.filters must be a non-empty string list")


def _read_report_excerpt(report_path: Path) -> str:
    if not report_path.exists():
        return ""
    lines = report_path.read_text(encoding="utf-8", errors="replace").splitlines()
    filtered = []
    for line in lines:
        if line.startswith("|") and filtered.count(line) > 1:
            continue
        filtered.append(line)
        if len(filtered) >= 35:
            break
    return "\n".join(filtered)


def _append_jsonl(path: Path, item: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(item, sort_keys=True) + "\n")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _run_id(created_at: str) -> str:
    return "".join(ch for ch in created_at if ch.isdigit())[:14]
