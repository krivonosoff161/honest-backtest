"""Safe LLM provider layer for the experimental Strategy Discovery Lab.

The default provider is a deterministic local stub. Live providers are opt-in
and guarded by call count, token, run-cost, and daily-cost limits.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .models import LLMConfig, LLMMessage, LLMRequest, LLMResponse


DEFAULT_ALIBABA_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
ALIBABA_BASE_URLS = {
    "singapore": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    "us": "https://dashscope-us.aliyuncs.com/compatible-mode/v1",
    "beijing": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "hong_kong": "https://cn-hongkong.dashscope.aliyuncs.com/compatible-mode/v1",
}


@dataclass(frozen=True)
class ModelPricing:
    input_usd_per_million: float
    output_usd_per_million: float


DEFAULT_PRICING: dict[str, ModelPricing] = {
    "qwen3.5-flash": ModelPricing(0.10, 0.40),
    "qwen3.5-plus": ModelPricing(0.40, 2.40),
    "qwen-plus": ModelPricing(0.40, 2.40),
    "qwen3-max": ModelPricing(1.20, 6.00),
    "qwen3-max-2026-01-23": ModelPricing(1.20, 6.00),
}


class LLMProvider(Protocol):
    name: str

    def complete(self, request: LLMRequest, config: LLMConfig) -> LLMResponse:
        """Return a model response for an already budget-checked request."""


def estimate_tokens(text: str) -> int:
    """Conservative token estimate without tokenizer dependencies."""
    if not text:
        return 0
    by_chars = (len(text) + 2) // 3
    by_words = max(1, len(text.split()))
    return max(by_chars, by_words)


def estimate_messages_tokens(messages: list[LLMMessage]) -> int:
    return sum(estimate_tokens(message.role) + estimate_tokens(message.content) + 4 for message in messages)


def pricing_for_model(model: str) -> ModelPricing:
    input_env = os.getenv(f"STRATEGY_LAB_PRICE_{_env_model_name(model)}_INPUT_USD_PER_M")
    output_env = os.getenv(f"STRATEGY_LAB_PRICE_{_env_model_name(model)}_OUTPUT_USD_PER_M")
    if input_env and output_env:
        return ModelPricing(float(input_env), float(output_env))
    return DEFAULT_PRICING.get(model, ModelPricing(0.40, 2.40))


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = pricing_for_model(model)
    return round(
        (input_tokens / 1_000_000) * pricing.input_usd_per_million
        + (output_tokens / 1_000_000) * pricing.output_usd_per_million,
        6,
    )


def make_request(
    provider: str,
    model: str,
    messages: list[LLMMessage],
    max_output_tokens: int,
    live: bool,
) -> LLMRequest:
    input_tokens = estimate_messages_tokens(messages)
    output_tokens = max_output_tokens
    estimated_usd = estimate_cost_usd(model, input_tokens, output_tokens)
    return LLMRequest(
        provider=provider,
        model=model,
        messages=messages,
        max_output_tokens=max_output_tokens,
        estimated_input_tokens=input_tokens,
        estimated_output_tokens=output_tokens,
        estimated_usd=estimated_usd,
        live=live,
    )


def validate_budget(request: LLMRequest, config: LLMConfig) -> None:
    if config.max_calls < 1:
        raise ValueError("max_calls must be >= 1")
    if request.estimated_input_tokens > config.max_input_tokens:
        raise ValueError(
            f"input token estimate {request.estimated_input_tokens} exceeds cap {config.max_input_tokens}"
        )
    if request.estimated_output_tokens > config.max_output_tokens:
        raise ValueError(
            f"output token estimate {request.estimated_output_tokens} exceeds cap {config.max_output_tokens}"
        )
    if request.estimated_usd > config.run_usd_cap:
        raise ValueError(f"estimated run cost {request.estimated_usd:.6f} exceeds cap {config.run_usd_cap:.6f}")
    if _looks_like_max_model(request.model) and not config.allow_max_model:
        raise ValueError("max-class model is blocked unless allow_max_model is true")
    spent_today = read_daily_spend(config.out_dir)
    if spent_today + request.estimated_usd > config.daily_usd_cap:
        raise ValueError(
            f"daily spend {spent_today:.6f} + estimate {request.estimated_usd:.6f} "
            f"exceeds cap {config.daily_usd_cap:.6f}"
        )


def validate_live_switches(config: LLMConfig) -> None:
    if not config.live:
        return
    if not config.accept_cost:
        raise ValueError("live calls require --i-accept-cost")
    if os.getenv("STRATEGY_LAB_LLM_ENABLED", "").lower() != "true":
        raise ValueError("live calls require STRATEGY_LAB_LLM_ENABLED=true")


def read_daily_spend(out_dir: Path) -> float:
    cost_dir = out_dir / "llm-costs"
    if not cost_dir.exists():
        return 0.0
    total = 0.0
    for path in cost_dir.glob("*.jsonl"):
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                item = json.loads(line)
                total += float(item.get("estimated_usd", 0.0))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    return round(total, 6)


class StubLLMProvider:
    name = "stub"

    def complete(self, request: LLMRequest, config: LLMConfig) -> LLMResponse:
        proposal = {
            "schema_version": 1,
            "proposal_type": "strategy_research_plan",
            "status": "draft",
            "source": "local_stub",
            "budget": {
                "max_calls": config.max_calls,
                "max_input_tokens": config.max_input_tokens,
                "max_output_tokens": config.max_output_tokens,
                "run_usd_cap": config.run_usd_cap,
            },
            "hypotheses": [
                {
                    "id": "stub_hypothesis_001",
                    "asset_group": "private_asset_group",
                    "strategy_family": "breakout_or_reversion_placeholder",
                    "filters": ["volatility_regime", "liquidity_filter", "timeframe_alignment"],
                    "next_action": "run deterministic simulation batch before any review",
                    "safety_note": "stub output is not a trading signal",
                }
            ],
        }
        text = json.dumps(proposal, indent=2, sort_keys=True)
        return LLMResponse(
            provider=self.name,
            model=request.model,
            text=text,
            input_tokens=request.estimated_input_tokens,
            output_tokens=estimate_tokens(text),
            estimated_usd=0.0,
            live=False,
            raw_usage={"stub": True},
        )


class AlibabaQwenProvider:
    name = "alibaba"

    def complete(self, request: LLMRequest, config: LLMConfig) -> LLMResponse:
        validate_live_switches(config)
        api_key = os.getenv(config.api_key_env, "")
        if not api_key:
            raise ValueError(f"missing API key env var: {config.api_key_env}")
        base_url = resolve_alibaba_base_url(config.base_url).rstrip("/")
        url = f"{base_url}/chat/completions"
        payload = {
            "model": request.model,
            "messages": [message.to_dict() for message in request.messages],
            "max_tokens": request.max_output_tokens,
            "temperature": 0.1,
            "stream": False,
        }
        data = json.dumps(payload).encode("utf-8")
        http_request = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(http_request, timeout=60) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"alibaba provider HTTP {exc.code}: {body[:500]}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"alibaba provider network error: {exc}") from exc
        text = _extract_chat_text(raw)
        usage = raw.get("usage") if isinstance(raw.get("usage"), dict) else {}
        input_tokens = int(usage.get("prompt_tokens") or request.estimated_input_tokens)
        output_tokens = int(usage.get("completion_tokens") or estimate_tokens(text))
        estimated_usd = estimate_cost_usd(request.model, input_tokens, output_tokens)
        return LLMResponse(
            provider=self.name,
            model=request.model,
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_usd=estimated_usd,
            live=True,
            raw_usage=usage,
        )


def provider_for_name(name: str) -> LLMProvider:
    normalized = name.strip().lower()
    if normalized == "stub":
        return StubLLMProvider()
    if normalized == "alibaba":
        return AlibabaQwenProvider()
    raise ValueError(f"unsupported LLM provider: {name}")


def resolve_alibaba_base_url(base_url: str = "") -> str:
    """Resolve the OpenAI-compatible Model Studio base URL.

    Region-specific API keys are not interchangeable, so callers can override
    the base URL directly or set DASHSCOPE_REGION to a known region name.
    """
    explicit = base_url or os.getenv("DASHSCOPE_BASE_URL", "")
    if explicit:
        return explicit.rstrip("/")
    region = os.getenv("DASHSCOPE_REGION", "").strip().lower().replace("-", "_")
    return ALIBABA_BASE_URLS.get(region, DEFAULT_ALIBABA_BASE_URL)


def alibaba_environment_report(base_url: str = "", api_key_env: str = "DASHSCOPE_API_KEY") -> dict[str, Any]:
    resolved_base_url = resolve_alibaba_base_url(base_url)
    region = os.getenv("DASHSCOPE_REGION", "").strip() or "default_singapore"
    key = os.getenv(api_key_env, "")
    enabled = os.getenv("STRATEGY_LAB_LLM_ENABLED", "").lower() == "true"
    return {
        "schema_version": 1,
        "provider": "alibaba",
        "api_key_env": api_key_env,
        "api_key_present": bool(key),
        "api_key_preview": _secret_preview(key),
        "live_switch_enabled": enabled,
        "region": region,
        "base_url": resolved_base_url,
        "known_regions": sorted(ALIBABA_BASE_URLS),
        "chat_completions_url": f"{resolved_base_url.rstrip('/')}/chat/completions",
    }


def _extract_chat_text(raw: dict[str, Any]) -> str:
    choices = raw.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("provider response has no choices")
    first = choices[0]
    if not isinstance(first, dict):
        raise RuntimeError("provider response choice is not an object")
    message = first.get("message")
    if not isinstance(message, dict):
        raise RuntimeError("provider response choice has no message")
    content = message.get("content")
    if not isinstance(content, str):
        raise RuntimeError("provider response message has no string content")
    return content


def _looks_like_max_model(model: str) -> bool:
    return "max" in model.lower()


def _env_model_name(model: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in model.upper())


def _secret_preview(secret: str) -> str:
    if not secret:
        return ""
    if len(secret) <= 8:
        return "***"
    return f"{secret[:4]}...{secret[-4:]}"
