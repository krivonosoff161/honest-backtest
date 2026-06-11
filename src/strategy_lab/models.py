"""Data records for the experimental Strategy Discovery Lab."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass(frozen=True)
class InventoryConfig:
    source_root: Path
    out_dir: Path
    tick_root: Optional[Path] = None
    run_id: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class FileSummary:
    run_id: str
    dataset: str
    root: str
    rel_path: str
    abs_path: str
    file_name: str
    ext: str
    compression: str
    size_bytes: int
    mtime_utc: str
    readable: bool = True
    error: str = ""
    schema_header: str = ""
    schema_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class InventoryResult:
    run_id: str
    created_at: str
    out_dir: Path
    manifest_path: Path
    latest_path: Path
    report_path: Path
    files_written: list[Path] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "created_at": self.created_at,
            "out_dir": str(self.out_dir),
            "manifest_path": str(self.manifest_path),
            "latest_path": str(self.latest_path),
            "report_path": str(self.report_path),
            "files_written": [str(path) for path in self.files_written],
        }


@dataclass(frozen=True)
class RegistryConfig:
    out_dir: Path
    run_id: Optional[str] = None
    created_at: Optional[str] = None


@dataclass(frozen=True)
class RegistryWriteResult:
    record_id: str
    created_at: str
    out_dir: Path
    record_path: Path
    index_path: Path

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "created_at": self.created_at,
            "out_dir": str(self.out_dir),
            "record_path": str(self.record_path),
            "index_path": str(self.index_path),
        }


@dataclass(frozen=True)
class ExperimentQueueConfig:
    out_dir: Path
    created_by: str = "human"
    run_id: Optional[str] = None
    created_at: Optional[str] = None


@dataclass(frozen=True)
class ExperimentQueueResult:
    experiment_id: str
    created_at: str
    out_dir: Path
    queue_path: Path
    index_path: Path

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "created_at": self.created_at,
            "out_dir": str(self.out_dir),
            "queue_path": str(self.queue_path),
            "index_path": str(self.index_path),
        }


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    model: str
    out_dir: Path
    run_id: Optional[str] = None
    live: bool = False
    accept_cost: bool = False
    max_calls: int = 1
    max_input_tokens: int = 8_000
    max_output_tokens: int = 1_000
    run_usd_cap: float = 0.10
    daily_usd_cap: float = 1.00
    allow_max_model: bool = False
    base_url: str = ""
    api_key_env: str = "DASHSCOPE_API_KEY"
    created_at: Optional[str] = None


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass(frozen=True)
class LLMRequest:
    provider: str
    model: str
    messages: list[LLMMessage]
    max_output_tokens: int
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_usd: float
    live: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "messages": [message.to_dict() for message in self.messages],
            "max_output_tokens": self.max_output_tokens,
            "estimated_input_tokens": self.estimated_input_tokens,
            "estimated_output_tokens": self.estimated_output_tokens,
            "estimated_usd": self.estimated_usd,
            "live": self.live,
        }


@dataclass(frozen=True)
class LLMResponse:
    provider: str
    model: str
    text: str
    input_tokens: int
    output_tokens: int
    estimated_usd: float
    live: bool
    raw_usage: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LLMRunResult:
    run_id: str
    created_at: str
    out_dir: Path
    request_path: Path
    response_path: Path
    proposal_path: Path
    cost_path: Path
    live: bool
    estimated_usd: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "created_at": self.created_at,
            "out_dir": str(self.out_dir),
            "request_path": str(self.request_path),
            "response_path": str(self.response_path),
            "proposal_path": str(self.proposal_path),
            "cost_path": str(self.cost_path),
            "live": self.live,
            "estimated_usd": self.estimated_usd,
        }
