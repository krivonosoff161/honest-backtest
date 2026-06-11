"""Path helpers for Strategy Discovery Lab inventory."""

from __future__ import annotations

from pathlib import Path


def ensure_output_layout(out_dir: Path) -> dict[str, Path]:
    """Create the private output folders used by inventory artifacts."""
    paths = {
        "manifests": out_dir / "manifests",
        "reports": out_dir / "reports",
        "registry": out_dir / "registry",
        "experiment_queue": out_dir / "experiments" / "queue",
        "experiment_running": out_dir / "experiments" / "running",
        "experiment_completed": out_dir / "experiments" / "completed",
        "experiment_failed": out_dir / "experiments" / "failed",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def relative_to_or_name(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return path.name
