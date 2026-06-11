# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from strategy_lab.cli import main  # noqa: E402
from strategy_lab.models import ExperimentQueueConfig, RegistryConfig  # noqa: E402
from strategy_lab.registry import append_registry_entry, initialize_registry, queue_experiment_plan  # noqa: E402


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8", newline="\n")
    return path


def _plan() -> dict:
    return {
        "schema_version": 1,
        "hypothesis": "Synthetic volatility expansion may improve a breakout family.",
        "asset_cluster": "synthetic_high_vol",
        "timeframes": ["5m"],
        "strategy_ids": ["volume_breakout"],
        "parameter_grid": {"lookback_bars": [20, 40]},
        "filters": {"benchmark_regime": ["not_down"]},
        "data_window": {
            "train": ["2000-01-01", "2000-02-01"],
            "validation": ["2000-02-02", "2000-03-01"],
            "forward": ["2000-03-02", "2000-04-01"],
        },
        "budgets": {
            "max_variants": 20,
            "max_runtime_seconds": 60,
            "llm_enabled": False,
        },
    }


def _entry() -> dict:
    return {
        "schema_version": 1,
        "strategy_id": "volume_breakout",
        "status": "needs_forward",
        "asset_cluster": "synthetic_high_vol",
        "market_regime": "synthetic_momentum",
        "timeframe": "5m",
        "filters": {"benchmark_regime": "not_down"},
        "works_when": ["relative volume is high"],
        "fails_when": ["liquidity is thin"],
        "evidence_refs": ["exp_test"],
        "review_notes": "Needs forward evidence before further attention.",
    }


def test_registry_init_creates_private_layout(tmp_path):
    result = initialize_registry(RegistryConfig(out_dir=tmp_path / "lab", created_at="2000-01-02T00:00:00Z"))
    assert Path(result["metadata_path"]).exists()
    assert (tmp_path / "lab" / "experiments" / "queue").exists()
    assert (tmp_path / "lab" / "experiments" / "completed").exists()


def test_queue_experiment_plan_writes_queue_record_and_index(tmp_path):
    plan_path = _write_json(tmp_path / "plan.json", _plan())
    result = queue_experiment_plan(
        plan_path,
        ExperimentQueueConfig(
            out_dir=tmp_path / "lab",
            run_id="test_run",
            created_at="2000-01-02T00:00:00Z",
        ),
    )
    assert result.experiment_id == "exp_test_run"
    queued = json.loads(result.queue_path.read_text(encoding="utf-8"))
    assert queued["status"] == "queued"
    assert queued["created_by"] == "human"
    assert queued["budgets"]["llm_enabled"] is False
    assert result.index_path.exists()


def test_queue_experiment_plan_rejects_llm_inside_runner(tmp_path):
    plan = _plan()
    plan["budgets"]["llm_enabled"] = True
    plan_path = _write_json(tmp_path / "bad_plan.json", plan)
    try:
        queue_experiment_plan(plan_path, ExperimentQueueConfig(out_dir=tmp_path / "lab"))
    except ValueError as exc:
        assert "LLM" in str(exc)
    else:
        raise AssertionError("expected LLM runner guard")


def test_append_registry_entry_rejects_approval_language(tmp_path):
    entry = _entry()
    entry["status"] = "approved"
    entry_path = _write_json(tmp_path / "bad_entry.json", entry)
    try:
        append_registry_entry(entry_path, RegistryConfig(out_dir=tmp_path / "lab"))
    except ValueError as exc:
        assert "status" in str(exc) or "blocked" in str(exc)
    else:
        raise AssertionError("expected registry status guard")


def test_append_registry_entry_writes_append_only_index(tmp_path):
    entry_path = _write_json(tmp_path / "entry.json", _entry())
    result = append_registry_entry(
        entry_path,
        RegistryConfig(
            out_dir=tmp_path / "lab",
            run_id="test_run",
            created_at="2000-01-02T00:00:00Z",
        ),
    )
    assert result.record_id == "reg_test_run"
    assert result.record_path.exists()
    lines = result.index_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["status"] == "needs_forward"


def test_registry_cli_init_add_and_queue(tmp_path, capsys):
    entry_path = _write_json(tmp_path / "entry.json", _entry())
    plan_path = _write_json(tmp_path / "plan.json", _plan())
    out_dir = tmp_path / "lab"

    assert main(["registry-init", "--out-dir", str(out_dir)]) == 0
    assert "registry metadata:" in capsys.readouterr().out

    assert main(["registry-add", "--entry", str(entry_path), "--out-dir", str(out_dir), "--run-id", "cli_reg"]) == 0
    assert "registry record: reg_cli_reg" in capsys.readouterr().out

    assert main(["queue-plan", "--plan", str(plan_path), "--out-dir", str(out_dir), "--run-id", "cli_exp"]) == 0
    assert "experiment queued: exp_cli_exp" in capsys.readouterr().out
