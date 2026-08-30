from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROJECTION = Path("docs/trading-portfolio-roadmap.yaml")
EXPECTED_HASH_CANONICALIZATION = "utf8_lf"
EXPECTED_GOVERNANCE = {
    "documentation_owner": "honest-backtest",
    "upstream_documentation_owner": "trading-bot-v2",
    "projection_role": "pinned_module_projection",
    "portfolio_integrator": "krivonosoff161",
}
EXPECTED_UPSTREAM_METADATA = {
    "repository": "krivonosoff161/trading-bot-v2",
    "schema": "TradingPortfolioRoadmap.v1",
}
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
PRIVATE_POINTER = re.compile(
    r"(?i)(?:[a-z]:\\users\\|(?:^|[/\\])\.env(?:$|[/\\])|"
    r"credential[_ -]?store|BEGIN [A-Z ]*PRIVATE KEY|[?&](?:token|key|secret)=)"
)
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
CURRENT_DOCUMENTS_CONTROLLED_PATHS = {
    "AGENTS.md",
    "ARCHITECTURE.md",
    "CURRENT_STATE.md",
    "README.md",
    "ROADMAP.md",
    ".github/workflows/tests.yml",
    "scripts/check_portfolio_docs.py",
    "tests/test_portfolio_docs.py",
}


def canonical_text_sha256(path: Path) -> str:
    """Hash UTF-8 text after normalizing checkout line endings to LF."""
    text = path.read_bytes().decode("utf-8")
    canonical = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_projection(root: Path) -> dict[str, Any]:
    value = json.loads((root / PROJECTION).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("portfolio projection must be an object")
    return value


def _git_output(root: Path, *args: str) -> str | None:
    """Return a bounded Git answer, or None when the path is not a Git checkout."""
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def _is_documentation_controlled_path(path: str) -> bool:
    return path in CURRENT_DOCUMENTS_CONTROLLED_PATHS or path.startswith("docs/")


def _implementation_snapshot_sha256(root: Path) -> str | None:
    """Hash the exact non-documentation Git tree currently under review.

    The projection's commit baseline remains useful for ordinary history, but a
    reviewed PR may be squash-merged and therefore receive a new commit object.
    Hashing the path, mode, object type, and blob identity keeps the review
    binding intact without treating a non-ancestor commit as a failure merely
    because GitHub rewrote the commit graph.
    """
    tree = _git_output(root, "ls-tree", "-r", "--full-tree", "HEAD")
    if tree is None:
        return None

    digest = hashlib.sha256()
    for line in tree.splitlines():
        metadata, separator, path = line.partition("\t")
        fields = metadata.split()
        if not separator or len(fields) != 3 or _is_documentation_controlled_path(path):
            continue
        mode, object_type, object_id = fields
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(mode.encode("ascii"))
        digest.update(b"\0")
        digest.update(object_type.encode("ascii"))
        digest.update(b"\0")
        digest.update(object_id.encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _uncontrolled_implementation_paths(root: Path, baseline: str) -> list[str] | None:
    """Find changes after the documentation baseline that need a new review.

    A current document records a preceding implementation baseline; it cannot
    silently certify later implementation edits in the same checkout. Fixtures
    without Git metadata return None because their projection tests verify
    structure only.
    """
    if _git_output(root, "rev-parse", "--is-inside-work-tree") != "true":
        return None
    if _git_output(root, "rev-parse", "--verify", f"{baseline}^{{commit}}") is None:
        return ["<unknown-baseline>"]
    if _git_output(root, "merge-base", "--is-ancestor", baseline, "HEAD") is None:
        return ["<non-ancestor-baseline>"]
    changed = _git_output(root, "diff", "--name-only", f"{baseline}..HEAD")
    if changed is None:
        return ["<diff-unavailable>"]
    return [path for path in changed.splitlines() if not _is_documentation_controlled_path(path)]


def _validate_upstream_head(
    upstream_roadmap: Path, expected_commit: str, failures: list[str]
) -> None:
    """Compare a supplied public source tree's exact HEAD with the pinned SHA."""
    upstream_root = _git_output(upstream_roadmap.parent, "rev-parse", "--show-toplevel")
    if upstream_root is None:
        return
    upstream_head = _git_output(Path(upstream_root), "rev-parse", "HEAD")
    if upstream_head != expected_commit:
        failures.append("upstream roadmap HEAD does not match pinned commit")


def _all_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        strings: list[str] = []
        for key, nested in value.items():
            strings.extend(_all_strings(key))
            strings.extend(_all_strings(nested))
        return strings
    if isinstance(value, (list, tuple)):
        strings = []
        for nested in value:
            strings.extend(_all_strings(nested))
        return strings
    return []


def _markdown_files(root: Path) -> list[Path]:
    excluded = {".git", ".venv", "venv", "build", "dist", "strategy-lab-data", "lab-runs"}
    return sorted(path for path in root.rglob("*.md") if not excluded.intersection(path.parts))


def _local_destination(source: Path, raw: str) -> Path | None:
    destination = raw.strip().split(maxsplit=1)[0].strip("<>")
    if not destination or "://" in destination or destination.startswith(("#", "mailto:")):
        return None
    return (source.parent / destination.split("#", maxsplit=1)[0]).resolve()


def validate(root: Path = ROOT, upstream_roadmap: Path | None = None) -> list[str]:
    failures: list[str] = []
    try:
        projection = load_projection(root)
    except (OSError, ValueError, json.JSONDecodeError):
        return ["portfolio projection is missing or invalid"]

    if projection.get("schema") != "TradingPortfolioRoadmapProjection.v1":
        failures.append("unexpected projection schema")
    if projection.get("status") != "current":
        failures.append("projection status must be current")
    for field, expected in EXPECTED_GOVERNANCE.items():
        if projection.get(field) != expected:
            failures.append(f"projection governance field mismatch: {field}")
    verified_against = str(projection.get("verified_against", ""))
    if not SHA40.fullmatch(verified_against):
        failures.append("projection repository baseline is not a full SHA")
    else:
        expected_snapshot = str(projection.get("implementation_snapshot_sha256", ""))
        uncontrolled = _uncontrolled_implementation_paths(root, verified_against)
        actual_snapshot = _implementation_snapshot_sha256(root)
        snapshot_matches = uncontrolled is None
        if not SHA256.fullmatch(expected_snapshot):
            failures.append("projection implementation snapshot is not a SHA-256")
        elif uncontrolled is not None and actual_snapshot is None:
            failures.append("projection implementation snapshot is unavailable")
        elif actual_snapshot is not None:
            snapshot_matches = actual_snapshot == expected_snapshot
            if not snapshot_matches:
                failures.append("projection implementation snapshot does not match checkout")
        if uncontrolled and not snapshot_matches:
            failures.append("documentation baseline has unreviewed implementation changes")

    upstream = projection.get("upstream")
    if not isinstance(upstream, dict):
        failures.append("upstream projection metadata missing")
    else:
        for field, expected in EXPECTED_UPSTREAM_METADATA.items():
            if upstream.get(field) != expected:
                failures.append(f"upstream metadata mismatch: {field}")
        if not isinstance(upstream.get("version"), str) or not upstream["version"]:
            failures.append("upstream version is missing or invalid")
        if upstream.get("hash_canonicalization") != EXPECTED_HASH_CANONICALIZATION:
            failures.append("upstream hash canonicalization mismatch")
        if not SHA40.fullmatch(str(upstream.get("commit_sha", ""))):
            failures.append("upstream commit is not a full SHA")
        if not SHA256.fullmatch(str(upstream.get("sha256", ""))):
            failures.append("upstream hash is not SHA-256")
        if upstream_roadmap is not None:
            try:
                actual_hash = canonical_text_sha256(upstream_roadmap)
            except (OSError, UnicodeDecodeError):
                failures.append("upstream roadmap could not be read")
            else:
                if actual_hash != upstream.get("sha256"):
                    failures.append("upstream roadmap content hash mismatch")
                else:
                    _validate_upstream_head(upstream_roadmap, str(upstream["commit_sha"]), failures)

        bridge = root / "docs" / "validation-bridge-contract.md"
        if not bridge.is_file():
            failures.append("validation bridge projection is missing")
        elif str(upstream.get("commit_sha", "")) not in bridge.read_text(
            encoding="utf-8", errors="replace"
        ):
            failures.append("validation bridge does not carry the pinned upstream commit")

    module = projection.get("module")
    if not isinstance(module, dict):
        failures.append("validator module projection missing")
    else:
        expected = {
            "module_id": "honest_backtest_validation",
            "owner_repository": "honest-backtest",
            "status": "implemented_bounded",
            "authority": "none",
        }
        for field, value in expected.items():
            if module.get(field) != value:
                failures.append(f"validator module {field} mismatch")
        evidence = module.get("implemented_evidence")
        if not isinstance(evidence, list) or not evidence:
            failures.append("validator module has no evidence")
        else:
            for raw_path in evidence:
                if not isinstance(raw_path, str) or not (root / raw_path).exists():
                    failures.append("validator evidence path is missing")
                    break

    for value in _all_strings(projection):
        if PRIVATE_POINTER.search(value):
            failures.append("projection contains a forbidden private pointer")
            break

    current_documents = projection.get("current_documents")
    if not isinstance(current_documents, list) or not current_documents:
        failures.append("current document registry missing")
    else:
        for raw_path in current_documents:
            if not isinstance(raw_path, str):
                failures.append("current document path must be a string")
                continue
            path = root / raw_path
            if not path.is_file():
                failures.append(f"current document missing: {raw_path}")
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for marker in (
                "Status: **CURRENT**",
                f"Verified: {projection.get('verified_date')}",
                verified_against,
            ):
                if marker not in text:
                    failures.append(f"current document lacks control metadata: {raw_path}")
                    break

    old_roadmap = root / "docs/strategy-lab-roadmap.md"
    historical = root / "docs/history/strategy-lab-roadmap.md"
    if old_roadmap.exists():
        failures.append("superseded Strategy Lab roadmap remains at current path")
    if not historical.is_file() or "HISTORICAL / SUPERSEDED" not in historical.read_text(encoding="utf-8"):
        failures.append("historical Strategy Lab roadmap is missing its banner")

    for source in _markdown_files(root):
        text = source.read_text(encoding="utf-8", errors="replace")
        for raw in MARKDOWN_LINK.findall(text):
            destination = _local_destination(source, raw)
            if destination is not None and not destination.exists():
                failures.append(f"broken documentation link: {source.relative_to(root)}")
                break
        if source != historical and "(strategy-lab-roadmap.md)" in text:
            failures.append(f"current document links to superseded roadmap: {source.relative_to(root)}")

    test_count = sum(
        1
        for path in (root / "tests").glob("test_*.py")
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("def test_")
    )
    documented_test_count = projection.get("documented_test_count")
    if not isinstance(documented_test_count, int) or documented_test_count < 1:
        failures.append("projection documented test count is missing or invalid")
    elif test_count != documented_test_count:
        failures.append(
            f"documented test count drifted: expected {documented_test_count}, found {test_count}"
        )

    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate honest-backtest portfolio documentation.")
    parser.add_argument(
        "--upstream-roadmap",
        type=Path,
        default=None,
        help="Optional public trading-bot-v2 roadmap file for direct SHA-256 alignment proof.",
    )
    args = parser.parse_args(argv)
    failures = validate(upstream_roadmap=args.upstream_roadmap)
    if failures:
        print("portfolio documentation guard: failed", file=sys.stderr)
        for failure in failures:
            print(f" - {failure}", file=sys.stderr)
        return 1
    print("portfolio documentation guard: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
