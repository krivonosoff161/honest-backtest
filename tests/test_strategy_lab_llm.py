# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from strategy_lab.cli import main  # noqa: E402
from strategy_lab.llm import AlibabaQwenProvider, alibaba_environment_report, make_request, validate_budget  # noqa: E402
from strategy_lab.llm_workflow import (  # noqa: E402
    build_inventory_digest,
    estimate_llm_plan,
    parse_and_validate_proposal,
    run_llm_plan,
)
from strategy_lab.models import LLMConfig, LLMMessage  # noqa: E402


def _private_inventory(tmp_path: Path) -> Path:
    out = tmp_path / "private"
    manifest = out / "manifests" / "inventory_test.json"
    report = out / "reports" / "inventory_test.md"
    latest = out / "manifests" / "inventory_latest.json"
    manifest.parent.mkdir(parents=True)
    report.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps(
            {
                "totals": {
                    "tick_files": 2,
                    "feature_files": 3,
                    "event_logs": 4,
                    "cache_files": 0,
                    "quality_warnings": 0,
                },
                "source_summaries": [
                    {"dataset": "tick_tape", "exists": True, "files": 2, "bytes": 100},
                    {"dataset": "feature_logs", "exists": True, "files": 3, "bytes": 200},
                ],
            }
        ),
        encoding="utf-8",
    )
    report.write_text(
        "# Strategy Lab Inventory\n\n"
        "- Tick files: 2\n"
        "- Feature files: 3\n"
        "- Quality warnings: 0\n",
        encoding="utf-8",
    )
    latest.write_text(
        json.dumps(
            {
                "run_id": "test",
                "created_at": "2000-01-02T00:00:00Z",
                "manifest_path": str(manifest),
                "report_path": str(report),
            }
        ),
        encoding="utf-8",
    )
    return latest


def test_llm_estimate_does_not_write_or_call_provider(tmp_path):
    latest = _private_inventory(tmp_path)
    result = estimate_llm_plan(
        latest,
        LLMConfig(provider="alibaba", model="qwen3.5-flash", out_dir=tmp_path / "llm"),
    )
    assert result["mode"] == "estimate"
    assert result["estimated_input_tokens"] > 0
    assert result["estimated_usd"] <= result["run_usd_cap"]
    assert not (tmp_path / "llm").exists()


def test_stub_llm_plan_writes_guarded_artifacts(tmp_path):
    latest = _private_inventory(tmp_path)
    result = run_llm_plan(
        latest,
        LLMConfig(
            provider="stub",
            model="qwen3.5-flash",
            out_dir=tmp_path / "llm",
            run_id="stub_run",
            created_at="2000-01-02T00:00:00Z",
        ),
    )
    assert result.live is False
    assert result.estimated_usd == 0.0
    assert result.request_path.exists()
    assert result.response_path.exists()
    assert result.proposal_path.exists()
    proposal = json.loads(result.proposal_path.read_text(encoding="utf-8"))
    assert proposal["proposal_type"] == "strategy_research_plan"
    assert proposal["status"] == "draft"
    assert (tmp_path / "llm" / "llm-costs" / "2000-01-02.jsonl").exists()


def test_llm_cli_estimate_and_plan(tmp_path, capsys):
    latest = _private_inventory(tmp_path)
    estimate_rc = main(
        [
            "llm-estimate",
            "--inventory-latest",
            str(latest),
            "--out-dir",
            str(tmp_path / "llm"),
            "--provider",
            "stub",
        ]
    )
    assert estimate_rc == 0
    assert "estimated USD" in capsys.readouterr().out

    plan_rc = main(
        [
            "llm-plan",
            "--inventory-latest",
            str(latest),
            "--out-dir",
            str(tmp_path / "llm"),
            "--provider",
            "stub",
            "--run-id",
            "cli_stub",
        ]
    )
    assert plan_rc == 0
    assert "proposal:" in capsys.readouterr().out


def test_llm_cli_doctor_reports_local_alibaba_setup(monkeypatch, capsys):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setenv("DASHSCOPE_REGION", "us")
    rc = main(["llm-doctor"])
    assert rc == 0
    output = capsys.readouterr().out
    assert "api key present: False" in output
    assert "dashscope-us.aliyuncs.com" in output


def test_alibaba_environment_report_redacts_key(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-1234567890abcdef")
    report = alibaba_environment_report()
    assert report["api_key_present"] is True
    assert report["api_key_preview"] == "sk-1...cdef"
    assert "1234567890" not in json.dumps(report)


def test_inventory_digest_reads_real_inventory_count_fields(tmp_path):
    latest = _private_inventory(tmp_path)
    latest_payload = json.loads(latest.read_text(encoding="utf-8"))
    manifest_path = Path(latest_payload["manifest_path"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_summaries"] = [{"dataset": "tick_tape", "exists": True, "file_count": 7, "byte_count": 1234}]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    digest = json.loads(build_inventory_digest(latest))
    assert digest["sources"][0]["files"] == 7
    assert digest["sources"][0]["bytes"] == 1234


def test_max_model_requires_explicit_allow(tmp_path):
    request = make_request(
        provider="alibaba",
        model="qwen3-max",
        messages=[LLMMessage("user", "small")],
        max_output_tokens=10,
        live=False,
    )
    try:
        validate_budget(
            request,
            LLMConfig(provider="alibaba", model="qwen3-max", out_dir=tmp_path),
        )
    except ValueError as exc:
        assert "max-class" in str(exc)
    else:
        raise AssertionError("expected max model guard")


def test_live_alibaba_requires_explicit_switches(tmp_path):
    latest = _private_inventory(tmp_path)
    try:
        run_llm_plan(
            latest,
            LLMConfig(
                provider="alibaba",
                model="qwen3.5-flash",
                out_dir=tmp_path / "llm",
                live=True,
                accept_cost=False,
            ),
        )
    except ValueError as exc:
        assert "--i-accept-cost" in str(exc)
    else:
        raise AssertionError("expected live switch guard")


def test_alibaba_provider_parses_openai_compatible_response(monkeypatch, tmp_path):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps(
                {
                    "choices": [{"message": {"content": '{"schema_version":1}'}}],
                    "usage": {"prompt_tokens": 12, "completion_tokens": 4},
                }
            ).encode("utf-8")

    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setenv("STRATEGY_LAB_LLM_ENABLED", "true")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    request = make_request(
        provider="alibaba",
        model="qwen3.5-flash",
        messages=[LLMMessage("user", "small")],
        max_output_tokens=10,
        live=True,
    )
    response = AlibabaQwenProvider().complete(
        request,
        LLMConfig(
            provider="alibaba",
            model="qwen3.5-flash",
            out_dir=tmp_path,
            live=True,
            accept_cost=True,
        ),
    )
    assert response.live is True
    assert response.input_tokens == 12
    assert response.output_tokens == 4
    assert captured["url"].endswith("/chat/completions")


def test_proposal_validation_rejects_non_draft():
    try:
        parse_and_validate_proposal(
            json.dumps(
                {
                    "schema_version": 1,
                    "proposal_type": "strategy_research_plan",
                    "status": "approved",
                    "hypotheses": [],
                }
            )
        )
    except ValueError as exc:
        assert "status" in str(exc)
    else:
        raise AssertionError("expected proposal validation error")
