from __future__ import annotations

import json
import os
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


# USD per 1M tokens. Keep this small catalog versioned in code so usage
# events keep cost data even when no pricing override is configured.
DEFAULT_CLAUDE_MODEL_PRICING: dict[str, dict[str, str]] = {
    "claude-haiku-4-5-20251001": {"input": "1", "output": "5"},
    "claude-haiku-4-5": {"input": "1", "output": "5"},
    "claude-sonnet-4-6": {"input": "3", "output": "15"},
    "default": {"input": "1", "output": "5"},
}


def get_optional_secret(name: str, default: str | None = None) -> str | None:
    """Read runtime config from env first, then Streamlit secrets."""
    value = os.getenv(name)
    if value:
        return value

    try:
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass

    return default


def get_model_token_pricing(model: str) -> dict[str, Decimal] | None:
    """Return USD-per-million-token pricing for a model when configured.

    Pricing changes over time, so we keep it in config/secrets instead of
    hard-coding vendor rates in application logic. Expected JSON shape:
    {"model-name": {"input": 1.0, "output": 5.0}}
    """
    pricing: dict[str, Any] = DEFAULT_CLAUDE_MODEL_PRICING
    raw = get_optional_secret("CLAUDE_MODEL_PRICING_JSON")

    if raw:
        try:
            override: dict[str, Any] = json.loads(raw)
            pricing = {**DEFAULT_CLAUDE_MODEL_PRICING, **override}
        except Exception:
            pricing = DEFAULT_CLAUDE_MODEL_PRICING

    model_pricing = pricing.get(model) or pricing.get("default")
    if not model_pricing:
        return None

    return {
        "input": Decimal(str(model_pricing["input"])),
        "output": Decimal(str(model_pricing["output"])),
    }


def calculate_llm_cost_usd(
    *,
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> dict[str, str | None]:
    """Calculate token costs from real usage and configured model pricing."""
    pricing = get_model_token_pricing(model)
    if not pricing:
        return {
            "input_cost_usd": None,
            "output_cost_usd": None,
            "total_cost_usd": None,
        }

    million = Decimal("1000000")
    input_cost = Decimal(input_tokens) / million * pricing["input"]
    output_cost = Decimal(output_tokens) / million * pricing["output"]
    total_cost = input_cost + output_cost

    def money(value: Decimal) -> str:
        return str(value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))

    return {
        "input_cost_usd": money(input_cost),
        "output_cost_usd": money(output_cost),
        "total_cost_usd": money(total_cost),
    }
