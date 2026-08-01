from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROJECTION = Path("docs/trading-portfolio-roadmap.yaml")
EXPECTED_REPOSITORY_SHA = "0f537a8fa0b80b17d100d38c0696f9a07d8e4ba6"
EXPECTED_UPSTREAM_SHA = "c20322f887977c5e3c3ec2c242ca560617d056fa"
EXPECTED_UPSTREAM_HASH = "9a16be5e6cc4a2c23c107579c60a1f89548bd55e5ed7619fdc1438c61eee3f64"
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
PRIVATE_POINTER = re.compile(
    r"(?i)(?:[a-z]:\\users\\|(?:^|[/\\])\.env(?:$|[/\\])|"
    r"credential[_ -]?store|BEGIN [A-Z ]*PRIVATE KEY|[?&](?:token|key|secret)=)"
)
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def load_projection(root: Path) -> dict[str, Any]:
    value = json.loads((root / PROJECTION).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("portfolio projection must be an object")
    return value


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
    if projection.get("verified_against") != EXPECTED_REPOSITORY_SHA:
        failures.append("projection repository SHA mismatch")

    upstream = projection.get("upstream")
    if not isinstance(upstream, dict):
        failures.append("upstream projection metadata missing")
    else:
        if upstream.get("commit_sha") != EXPECTED_UPSTREAM_SHA:
            failures.append("upstream commit mismatch")
        if upstream.get("sha256") != EXPECTED_UPSTREAM_HASH:
            failures.append("upstream roadmap hash mismatch")
        if not SHA40.fullmatch(str(upstream.get("commit_sha", ""))):
            failures.append("upstream commit is not a full SHA")
        if not SHA256.fullmatch(str(upstream.get("sha256", ""))):
            failures.append("upstream hash is not SHA-256")
        if upstream_roadmap is not None:
            try:
                actual_hash = hashlib.sha256(upstream_roadmap.read_bytes()).hexdigest()
            except OSError:
                failures.append("upstream roadmap could not be read")
            else:
                if actual_hash != upstream.get("sha256"):
                    failures.append("upstream roadmap content hash mismatch")

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
            for marker in ("Status: **CURRENT**", "Verified: 2026-08-01", EXPECTED_REPOSITORY_SHA):
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
    if test_count != 68:
        failures.append(f"documented test count drifted: expected 68, found {test_count}")

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
