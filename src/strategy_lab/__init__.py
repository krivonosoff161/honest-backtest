"""Experimental Strategy Discovery Lab utilities.

This package is intentionally separate from ``backtest_sanity``. It is not
part of the stable validation API.
"""

from .inventory import run_inventory
from .llm_workflow import estimate_llm_plan, run_llm_plan
from .registry import append_registry_entry, initialize_registry, queue_experiment_plan

__all__ = [
    "append_registry_entry",
    "estimate_llm_plan",
    "initialize_registry",
    "queue_experiment_plan",
    "run_inventory",
    "run_llm_plan",
]
