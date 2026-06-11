"""CLI for the experimental Strategy Discovery Lab."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from .inventory import run_inventory
from .llm_workflow import estimate_llm_plan, run_llm_plan
from .models import ExperimentQueueConfig, InventoryConfig, LLMConfig, RegistryConfig
from .registry import append_registry_entry, initialize_registry, queue_experiment_plan


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="strategy-lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inventory = subparsers.add_parser("inventory", help="Build a read-only local data inventory.")
    inventory.add_argument("--source-root", required=True, type=Path, help="Read-only source repo/root to inspect.")
    inventory.add_argument("--tick-root", type=Path, default=None, help="Optional read-only tick tape root.")
    inventory.add_argument("--out-dir", required=True, type=Path, help="Private output directory for manifests/reports.")
    inventory.add_argument("--run-id", default=None, help="Optional deterministic run id for tests/reproducibility.")

    registry_init = subparsers.add_parser("registry-init", help="Create private registry and queue folders.")
    registry_init.add_argument("--out-dir", required=True, type=Path, help="Private strategy-lab output directory.")
    registry_init.add_argument("--run-id", default=None, help="Optional deterministic run id.")

    registry_add = subparsers.add_parser("registry-add", help="Validate and append a registry entry.")
    registry_add.add_argument("--entry", required=True, type=Path, help="Registry entry JSON file.")
    registry_add.add_argument("--out-dir", required=True, type=Path, help="Private strategy-lab output directory.")
    registry_add.add_argument("--run-id", default=None, help="Optional deterministic run id.")

    queue_plan = subparsers.add_parser("queue-plan", help="Validate and queue an experiment plan.")
    queue_plan.add_argument("--plan", required=True, type=Path, help="Experiment plan JSON file.")
    queue_plan.add_argument("--out-dir", required=True, type=Path, help="Private strategy-lab output directory.")
    queue_plan.add_argument("--created-by", default="human", choices=["human", "rule", "llm"], help="Plan author.")
    queue_plan.add_argument("--run-id", default=None, help="Optional deterministic run id.")

    estimate = subparsers.add_parser("llm-estimate", help="Estimate a guarded LLM planning request without network.")
    _add_llm_args(estimate, live_args=False)

    plan = subparsers.add_parser("llm-plan", help="Create a guarded LLM research proposal.")
    _add_llm_args(plan, live_args=True)

    args = parser.parse_args(argv)
    if args.command == "inventory":
        result = run_inventory(
            InventoryConfig(
                source_root=args.source_root,
                tick_root=args.tick_root,
                out_dir=args.out_dir,
                run_id=args.run_id,
            )
        )
        print(f"inventory run: {result.run_id}")
        print(f"manifest: {result.manifest_path}")
        print(f"report: {result.report_path}")
        return 0
    if args.command == "registry-init":
        result = initialize_registry(
            RegistryConfig(
                out_dir=args.out_dir,
                run_id=args.run_id,
            )
        )
        print(f"registry metadata: {result['metadata_path']}")
        print(f"experiment queue: {result['queue_path']}")
        return 0
    if args.command == "registry-add":
        result = append_registry_entry(
            args.entry,
            RegistryConfig(
                out_dir=args.out_dir,
                run_id=args.run_id,
            ),
        )
        print(f"registry record: {result.record_id}")
        print(f"record: {result.record_path}")
        print(f"index: {result.index_path}")
        return 0
    if args.command == "queue-plan":
        result = queue_experiment_plan(
            args.plan,
            ExperimentQueueConfig(
                out_dir=args.out_dir,
                created_by=args.created_by,
                run_id=args.run_id,
            ),
        )
        print(f"experiment queued: {result.experiment_id}")
        print(f"plan: {result.queue_path}")
        print(f"index: {result.index_path}")
        return 0
    if args.command == "llm-estimate":
        estimate_result = estimate_llm_plan(
            args.inventory_latest,
            _llm_config_from_args(args, live=False),
        )
        print(f"provider: {estimate_result['provider']}")
        print(f"model: {estimate_result['model']}")
        print(f"estimated input tokens: {estimate_result['estimated_input_tokens']}")
        print(f"estimated output tokens: {estimate_result['estimated_output_tokens']}")
        print(f"estimated USD: {estimate_result['estimated_usd']:.6f}")
        print(f"run cap USD: {estimate_result['run_usd_cap']:.6f}")
        return 0
    if args.command == "llm-plan":
        result = run_llm_plan(
            args.inventory_latest,
            _llm_config_from_args(args, live=args.live),
        )
        print(f"llm run: {result.run_id}")
        print(f"live: {result.live}")
        print(f"estimated USD: {result.estimated_usd:.6f}")
        print(f"request: {result.request_path}")
        print(f"response: {result.response_path}")
        print(f"proposal: {result.proposal_path}")
        print(f"cost ledger: {result.cost_path}")
        return 0
    parser.error(f"unknown command: {args.command}")
    return 2


def _add_llm_args(parser: argparse.ArgumentParser, live_args: bool) -> None:
    parser.add_argument("--inventory-latest", required=True, type=Path, help="Private inventory_latest.json path.")
    parser.add_argument("--out-dir", required=True, type=Path, help="Private output directory for LLM artifacts.")
    parser.add_argument("--provider", default="stub", choices=["stub", "alibaba"], help="LLM provider.")
    parser.add_argument("--model", default="qwen3.5-flash", help="Model name for the provider.")
    parser.add_argument("--run-id", default=None, help="Optional deterministic run id.")
    parser.add_argument("--max-calls", type=int, default=1, help="Maximum model calls for this run.")
    parser.add_argument("--max-input-tokens", type=int, default=8_000, help="Input token estimate cap.")
    parser.add_argument("--max-output-tokens", type=int, default=1_000, help="Output token cap.")
    parser.add_argument("--run-usd-cap", type=float, default=0.10, help="Per-run estimated cost cap.")
    parser.add_argument("--daily-usd-cap", type=float, default=1.00, help="Daily estimated cost cap.")
    parser.add_argument("--allow-max-model", action="store_true", help="Allow max-class models for this run.")
    parser.add_argument("--base-url", default="", help="Optional provider base URL override.")
    parser.add_argument("--api-key-env", default="DASHSCOPE_API_KEY", help="Environment variable containing API key.")
    if live_args:
        parser.add_argument("--live", action="store_true", help="Allow a live provider call.")
        parser.add_argument("--i-accept-cost", action="store_true", help="Required for live provider calls.")


def _llm_config_from_args(args: argparse.Namespace, live: bool) -> LLMConfig:
    return LLMConfig(
        provider=args.provider,
        model=args.model,
        out_dir=args.out_dir,
        run_id=args.run_id,
        live=live,
        accept_cost=getattr(args, "i_accept_cost", False),
        max_calls=args.max_calls,
        max_input_tokens=args.max_input_tokens,
        max_output_tokens=args.max_output_tokens,
        run_usd_cap=args.run_usd_cap,
        daily_usd_cap=args.daily_usd_cap,
        allow_max_model=args.allow_max_model,
        base_url=args.base_url,
        api_key_env=args.api_key_env,
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
