# -*- coding: utf-8 -*-
import gzip
import ast
import json
import os
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from strategy_lab.cli import main  # noqa: E402
from strategy_lab.inventory import run_inventory  # noqa: E402
from strategy_lab.models import InventoryConfig  # noqa: E402


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_gz(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        handle.write(text)


def _make_source_tree(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "source"
    tick_root = tmp_path / "ticks"
    _write(
        tick_root / "SYNTH-A" / "2000-01-01.csv",
        "ts_ms,recv_ts_ms,symbol,side,price,size,trade_id\n"
        "1,2,SYNTH-A,buy,10,1,t1\n"
        "3,4,SYNTH-A,sell,11,2,t2\n",
    )
    _write_gz(
        source / "logs" / "features" / "5m" / "SYNTH-A" / "2000-01-01.csv.gz",
        "schema_version,ts_ms,ts,symbol,base_symbol,tf,open,high,low,close,volume_contracts,volume_usdt,regime\n"
        "1,10,2000-01-01T00:05:00Z,SYNTH-A,SYNTH-A,5m,1,2,1,2,100,200,trend\n",
    )
    _write(
        source / "logs" / "signals" / "main_signals.jsonl",
        json.dumps({"id": "sig1", "ts": "2000-01-01T00:00:00Z", "symbol": "SYNTH-A", "source": "test"}) + "\n",
    )
    _write(
        source / "logs" / "scout" / "scanner_journal.jsonl",
        json.dumps({"card_id": "card1", "ts_utc": "2000-01-01T00:00:00Z", "asset": "SYNTH-A", "source": "test"}) + "\n",
    )
    _write(source / "logs_archive" / "old.jsonl", json.dumps({"id": "old1", "ts": "1999-01-01T00:00:00Z"}) + "\n")
    _write(source / "scripts" / "backtest" / "backtest_runs" / "summary.json", json.dumps({"result": "placeholder"}))
    _write(source / "scripts" / "analysis" / "research" / "note.md", "# Synthetic note\n")
    _write(source / "scripts" / "backtest_candle_cache_65d.pkl", "do not unpickle")
    return source, tick_root


def test_inventory_scans_known_roots_without_mutating_sources(tmp_path):
    source, tick_root = _make_source_tree(tmp_path)
    watched = tick_root / "SYNTH-A" / "2000-01-01.csv"
    before = watched.read_text(encoding="utf-8")
    before_mtime = os.stat(watched).st_mtime_ns

    result = run_inventory(
        InventoryConfig(
            source_root=source,
            tick_root=tick_root,
            out_dir=tmp_path / "lab",
            run_id="test_run",
            created_at="2000-01-02T00:00:00Z",
        )
    )

    assert result.run_id == "test_run"
    assert watched.read_text(encoding="utf-8") == before
    assert os.stat(watched).st_mtime_ns == before_mtime


def test_inventory_writes_manifest_and_summary_to_out_dir(tmp_path):
    source, tick_root = _make_source_tree(tmp_path)
    out = tmp_path / "lab"

    result = run_inventory(
        InventoryConfig(
            source_root=source,
            tick_root=tick_root,
            out_dir=out,
            run_id="test_run",
            created_at="2000-01-02T00:00:00Z",
        )
    )

    assert result.manifest_path == out / "manifests" / "inventory_test_run.json"
    assert result.report_path == out / "reports" / "inventory_test_run.md"
    assert (out / "manifests" / "tape_files_test_run.csv").exists()
    assert (out / "manifests" / "feature_files_test_run.csv").exists()
    assert (out / "manifests" / "event_logs_test_run.csv").exists()
    assert (out / "manifests" / "cache_files_test_run.csv").exists()
    assert (out / "reports" / "coverage_by_symbol_test_run.csv").exists()
    assert (out / "reports" / "quality_warnings_test_run.csv").exists()


def test_inventory_handles_missing_optional_roots(tmp_path):
    source = tmp_path / "source"
    source.mkdir()

    result = run_inventory(
        InventoryConfig(
            source_root=source,
            tick_root=tmp_path / "missing_ticks",
            out_dir=tmp_path / "lab",
            run_id="missing",
            created_at="2000-01-02T00:00:00Z",
        )
    )
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["totals"]["quality_warnings"] >= 1
    assert manifest["totals"]["tick_files"] == 0


def test_inventory_refuses_to_write_inside_source_root(tmp_path):
    source, tick_root = _make_source_tree(tmp_path)
    try:
        run_inventory(
            InventoryConfig(
                source_root=source,
                tick_root=tick_root,
                out_dir=source / "reports",
                run_id="bad",
                created_at="2000-01-02T00:00:00Z",
            )
        )
    except ValueError as exc:
        assert "source_root" in str(exc)
    else:
        raise AssertionError("expected output boundary error")


def test_inventory_refuses_to_write_inside_tick_root(tmp_path):
    source, tick_root = _make_source_tree(tmp_path)
    try:
        run_inventory(
            InventoryConfig(
                source_root=source,
                tick_root=tick_root,
                out_dir=tick_root / "reports",
                run_id="bad",
                created_at="2000-01-02T00:00:00Z",
            )
        )
    except ValueError as exc:
        assert "tick_root" in str(exc)
    else:
        raise AssertionError("expected output boundary error")


def test_inventory_does_not_import_live_or_llm_modules():
    forbidden = {
        "src.scout.scanner_v0",
        "src.strategy.signal_engine",
        "scripts.auto_execute",
        "openai",
        "anthropic",
    }
    assert not (forbidden & set(sys.modules))


def test_strategy_lab_python_imports_stay_quarantined():
    forbidden_roots = {
        "aiohttp",
        "anthropic",
        "ccxt",
        "openai",
        "requests",
        "src",
        "scripts",
        "websockets",
    }
    for path in (_SRC / "strategy_lab").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = {alias.name.split(".")[0] for alias in node.names}
                assert not (names & forbidden_roots), (path, names & forbidden_roots)
            if isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".")[0]
                assert root not in forbidden_roots, (path, root)


def test_public_docs_do_not_expose_private_markers():
    forbidden = [
        "C:\\Users\\krivo",
        "trading-bot-v2",
        "PEPE",
        "DOGE",
        "BTC-USDT",
        "OKX",
        "ready to trade",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in (_SRC.parents[0] / "docs").glob("strategy*.md"))
    text += "\n" + (_SRC.parents[0] / "README.md").read_text(encoding="utf-8")
    text += "\n" + (_SRC.parents[0] / "docs" / "project-map.md").read_text(encoding="utf-8")
    text += "\n" + (_SRC.parents[0] / "docs" / "use-cases.md").read_text(encoding="utf-8")
    for marker in forbidden:
        assert marker not in text


def test_strategy_lab_source_does_not_expose_private_markers():
    forbidden = [
        "C:\\Users\\krivo",
        "trading-bot-v2",
        "PEPE",
        "DOGE",
        "BTC-USDT",
        "OKX",
        "okx",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in (_SRC / "strategy_lab").glob("*.py"))
    for marker in forbidden:
        assert marker not in text


def test_inventory_summary_contains_counts_not_raw_rows(tmp_path):
    source, tick_root = _make_source_tree(tmp_path)
    result = run_inventory(
        InventoryConfig(
            source_root=source,
            tick_root=tick_root,
            out_dir=tmp_path / "lab",
            run_id="summary",
            created_at="2000-01-02T00:00:00Z",
        )
    )
    summary = result.report_path.read_text(encoding="utf-8")
    assert "Tick files: 1" in summary
    assert "SYNTH-A" in summary
    assert "buy,10,1,t1" not in summary


def test_cli_inventory_command(tmp_path, capsys):
    source, tick_root = _make_source_tree(tmp_path)
    rc = main(
        [
            "inventory",
            "--source-root",
            str(source),
            "--tick-root",
            str(tick_root),
            "--out-dir",
            str(tmp_path / "lab"),
            "--run-id",
            "cli",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert "inventory run: cli" in captured.out
