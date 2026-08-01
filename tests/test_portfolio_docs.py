from __future__ import annotations

import json
from pathlib import Path

from scripts.check_portfolio_docs import (
    EXPECTED_GOVERNANCE,
    EXPECTED_REPOSITORY_SHA,
    EXPECTED_UPSTREAM_HASH,
    EXPECTED_UPSTREAM_SHA,
    validate,
)


def _fixture_root(tmp_path: Path) -> Path:
    (tmp_path / "docs/history").mkdir(parents=True)
    (tmp_path / "src/backtest_sanity").mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    current = "\n".join(
        [
            "# Current",
            "",
            "Status: **CURRENT**",
            "",
            "- Verified: 2026-08-01",
            f"- Verified against: `{EXPECTED_REPOSITORY_SHA}`",
        ]
    )
    (tmp_path / "README.md").write_text(current, encoding="utf-8")
    (tmp_path / "docs/trading-portfolio-roadmap.md").write_text(current, encoding="utf-8")
    (tmp_path / "docs/history/strategy-lab-roadmap.md").write_text(
        "# History\n\nStatus: **HISTORICAL / SUPERSEDED**\n", encoding="utf-8"
    )
    (tmp_path / "tests/test_contract.py").write_text(
        "\n".join(f"def test_{index}():\n    pass" for index in range(68)),
        encoding="utf-8",
    )
    projection = {
        "schema": "TradingPortfolioRoadmapProjection.v1",
        "version": "2026.08.01",
        "status": "current",
        "verified_date": "2026-08-01",
        **EXPECTED_GOVERNANCE,
        "verified_against": EXPECTED_REPOSITORY_SHA,
        "upstream": {
            "repository": "example/trading-bot-v2",
            "schema": "TradingPortfolioRoadmap.v1",
            "version": "2026.08.01",
            "commit_sha": EXPECTED_UPSTREAM_SHA,
            "sha256": EXPECTED_UPSTREAM_HASH,
        },
        "module": {
            "module_id": "honest_backtest_validation",
            "owner_repository": "honest-backtest",
            "purpose": "synthetic validator fixture",
            "status": "implemented_bounded",
            "authority": "none",
            "dependencies": [],
            "implemented_evidence": ["src/backtest_sanity"],
            "missing_evidence": "future evidence",
            "next_gate": "review",
            "public_private_boundary": "synthetic only",
        },
        "current_documents": ["README.md", "docs/trading-portfolio-roadmap.md"],
        "absolute_boundaries": ["no execution"],
    }
    (tmp_path / "docs/trading-portfolio-roadmap.yaml").write_text(
        json.dumps(projection), encoding="utf-8"
    )
    return tmp_path


def _projection(root: Path) -> dict[str, object]:
    return json.loads((root / "docs/trading-portfolio-roadmap.yaml").read_text(encoding="utf-8"))


def _write_projection(root: Path, projection: dict[str, object]) -> None:
    (root / "docs/trading-portfolio-roadmap.yaml").write_text(
        json.dumps(projection), encoding="utf-8"
    )


def test_repository_portfolio_documentation_contract_is_valid() -> None:
    assert validate() == []


def test_projection_cannot_grant_validator_authority(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    projection = _projection(root)
    projection["module"]["authority"] = "paper_only"  # type: ignore[index]
    _write_projection(root, projection)
    assert "validator module authority mismatch" in validate(root)

    for field in EXPECTED_GOVERNANCE:
        root = _fixture_root(tmp_path / field)
        projection = _projection(root)
        projection[field] = "synthetic-mismatch"
        _write_projection(root, projection)
        assert f"projection governance field mismatch: {field}" in validate(root)


def test_projection_requires_existing_evidence(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    projection = _projection(root)
    projection["module"]["implemented_evidence"] = ["missing.py"]  # type: ignore[index]
    _write_projection(root, projection)
    assert "validator evidence path is missing" in validate(root)


def test_private_pointer_is_rejected_without_echoing_value(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    projection = _projection(root)
    synthetic_pointer = "X:\\Users\\sample\\private-store"
    projection["synthetic"] = synthetic_pointer
    _write_projection(root, projection)
    failures = validate(root)
    assert "projection contains a forbidden private pointer" in failures
    assert synthetic_pointer not in "\n".join(failures)


def test_current_document_requires_control_metadata(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    (root / "README.md").write_text("# uncontrolled\n", encoding="utf-8")
    assert "current document lacks control metadata: README.md" in validate(root)


def test_superseded_roadmap_cannot_remain_current(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    (root / "docs/strategy-lab-roadmap.md").write_text("# stale\n", encoding="utf-8")
    assert "superseded Strategy Lab roadmap remains at current path" in validate(root)


def test_direct_upstream_hash_mismatch_is_rejected(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path / "repo")
    upstream = tmp_path / "upstream.yaml"
    upstream.write_text("synthetic different roadmap\n", encoding="utf-8")
    assert "upstream roadmap content hash mismatch" in validate(root, upstream)
