from __future__ import annotations

import hashlib
import json
from pathlib import Path

import scripts.check_portfolio_docs as docs_guard
from scripts.check_portfolio_docs import EXPECTED_GOVERNANCE, canonical_text_sha256, validate


SYNTHETIC_REPOSITORY_SHA = "1" * 40
SYNTHETIC_UPSTREAM_SHA = "2" * 40
SYNTHETIC_UPSTREAM_HASH = "3" * 64


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
            "- Verified: 2026-08-29",
            f"- Verified against: `{SYNTHETIC_REPOSITORY_SHA}`",
        ]
    )
    (tmp_path / "README.md").write_text(current, encoding="utf-8")
    (tmp_path / "docs/trading-portfolio-roadmap.md").write_text(current, encoding="utf-8")
    (tmp_path / "docs/validation-bridge-contract.md").write_text(
        f"# Bridge\n\nPinned upstream: `{SYNTHETIC_UPSTREAM_SHA}`\n", encoding="utf-8"
    )
    (tmp_path / "docs/history/strategy-lab-roadmap.md").write_text(
        "# History\n\nStatus: **HISTORICAL / SUPERSEDED**\n", encoding="utf-8"
    )
    (tmp_path / "tests/test_contract.py").write_text(
        "\n".join(f"def test_{index}():\n    pass" for index in range(70)),
        encoding="utf-8",
    )
    projection = {
        "schema": "TradingPortfolioRoadmapProjection.v1",
        "version": "2026.08.29",
        "status": "current",
        "verified_date": "2026-08-29",
        **EXPECTED_GOVERNANCE,
        "verified_against": SYNTHETIC_REPOSITORY_SHA,
        "upstream": {
            "repository": "krivonosoff161/trading-bot-v2",
            "schema": "TradingPortfolioRoadmap.v1",
            "version": "2026.08.29",
            "commit_sha": SYNTHETIC_UPSTREAM_SHA,
            "hash_canonicalization": "utf8_lf",
            "sha256": SYNTHETIC_UPSTREAM_HASH,
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
        "documented_test_count": 70,
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


def test_projection_requires_canonical_upstream_identity(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    projection = _projection(root)
    projection["upstream"]["repository"] = "synthetic/other"  # type: ignore[index]
    _write_projection(root, projection)
    assert "upstream metadata mismatch: repository" in validate(root)


def test_validation_bridge_must_carry_the_pinned_upstream_commit(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    (root / "docs/validation-bridge-contract.md").write_text("# unpinned\n", encoding="utf-8")
    assert "validation bridge does not carry the pinned upstream commit" in validate(root)


def test_documentation_baseline_rejects_unreviewed_implementation_changes(
    tmp_path: Path, monkeypatch
) -> None:
    root = _fixture_root(tmp_path)

    def fake_git_output(path: Path, *args: str) -> str | None:
        if args == ("rev-parse", "--is-inside-work-tree"):
            return "true"
        if args[:3] == ("rev-parse", "--verify", f"{SYNTHETIC_REPOSITORY_SHA}^{{commit}}"):
            return SYNTHETIC_REPOSITORY_SHA
        if args == ("merge-base", "--is-ancestor", SYNTHETIC_REPOSITORY_SHA, "HEAD"):
            return ""
        if args == ("diff", "--name-only", f"{SYNTHETIC_REPOSITORY_SHA}..HEAD"):
            return "src/backtest_sanity/new_implementation.py\n"
        return None

    monkeypatch.setattr(docs_guard, "_git_output", fake_git_output)
    assert "documentation baseline has unreviewed implementation changes" in validate(root)


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


def test_checked_out_upstream_head_mismatch_is_rejected(
    tmp_path: Path, monkeypatch
) -> None:
    root = _fixture_root(tmp_path / "repo")
    upstream = tmp_path / "upstream.yaml"
    upstream.write_text("synthetic upstream roadmap\n", encoding="utf-8")
    projection = _projection(root)
    projection["upstream"]["sha256"] = canonical_text_sha256(upstream)  # type: ignore[index]
    _write_projection(root, projection)

    def fake_git_output(path: Path, *args: str) -> str | None:
        if path == upstream.parent and args == ("rev-parse", "--show-toplevel"):
            return str(upstream.parent)
        if path == upstream.parent and args == ("rev-parse", "HEAD"):
            return "f" * 40
        return None

    monkeypatch.setattr(docs_guard, "_git_output", fake_git_output)
    assert "upstream roadmap HEAD does not match pinned commit" in validate(root, upstream)


def test_upstream_hash_is_portable_across_lf_and_crlf(tmp_path: Path) -> None:
    lf = tmp_path / "lf.yaml"
    crlf = tmp_path / "crlf.yaml"
    lf.write_bytes(b"schema: synthetic\nvalue: one\n")
    crlf.write_bytes(b"schema: synthetic\r\nvalue: one\r\n")

    expected = hashlib.sha256(b"schema: synthetic\nvalue: one\n").hexdigest()

    assert canonical_text_sha256(lf) == expected
    assert canonical_text_sha256(crlf) == expected


def test_upstream_hash_changes_when_content_changes(tmp_path: Path) -> None:
    original = tmp_path / "original.yaml"
    changed = tmp_path / "changed.yaml"
    original.write_text("status: current\n", encoding="utf-8")
    changed.write_text("status: superseded\n", encoding="utf-8")

    assert canonical_text_sha256(original) != canonical_text_sha256(changed)
