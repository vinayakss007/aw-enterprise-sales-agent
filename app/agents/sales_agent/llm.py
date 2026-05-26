"""LLM provider abstraction.

Two providers ship today:

* ``FakeLLM`` — deterministic offline provider used by tests and as the
  default when no ``OPENAI_API_KEY`` is set. Generates plausible-looking text
  from the prompt so downstream nodes can be tested end-to-end without
  spending money.
* ``OpenAILLM`` — real OpenAI provider, activated when ``LLM_PROVIDER=openai``
  and ``OPENAI_API_KEY`` is set. The ``openai`` package is imported lazily so
  the provider gracefully falls back to ``FakeLLM`` if the package isn't
  installed.

Both providers expose the same ``async complete(messages, ...) -> LLMResult``
contract so the agent nodes don't care which one they're talking to.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMResult:
    """A single LLM completion's content plus accounting."""

    content: str
    tokens_input: int = 0
    tokens_output: int = 0
    cost_cents: int = 0
    model: str = ""
    raw: Any | None = field(default=None, repr=False)


class LLMProvider(Protocol):
    model: str

    async def complete(
        self,
        messages: list[dict],
        *,
        max_tokens: int = 512,
        temperature: float = 0.4,
    ) -> LLMResult: ...


def _approx_token_count(text: str) -> int:
    """Rough token count — ~4 chars per token is a fine approximation."""
    return max(1, len(text) // 4)


class FakeLLM:
    """Deterministic offline provider used in tests and as the safe default."""

    model = "fake-llm-1"

    async def complete(
        self,
        messages: list[dict],
        *,
        max_tokens: int = 512,
        temperature: float = 0.4,
    ) -> LLMResult:
        # Concatenate all message contents into the "input" we account for.
        joined_input = "\n".join(
            str(m.get("content", "")) for m in messages if isinstance(m, dict)
        )
        # Use last user-style message as the seed for the fake reply so that
        # the same prompt always yields the same output.
        seed_text = messages[-1].get("content", "") if messages else ""
        seed_text = str(seed_text).strip()
        digest = hashlib.sha256(seed_text.encode("utf-8")).hexdigest()[:8]
        body = (
            f"[fake-llm:{digest}] "
            f"Based on the input ({len(seed_text)} chars), here is a generated response. "
            f"This text exists so the agent can be tested without a real model."
        )
        tokens_input = _approx_token_count(joined_input)
        tokens_output = _approx_token_count(body)
        return LLMResult(
            content=body,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            # FakeLLM is free; cost is zero.
            cost_cents=0,
            model=self.model,
        )


class OpenAILLM:
    """OpenAI Chat Completions provider.

    Pricing in USD/1M tokens for the default models is hard-coded as a starting
    point; production code should pull this from a config table per tenant.
    """

    # USD per 1M tokens — keep this list short and easy to update.
    _PRICING: dict[str, tuple[float, float]] = {
        "gpt-4o-mini": (0.15, 0.60),
        "gpt-4o": (2.50, 10.00),
        "gpt-4-turbo": (10.00, 30.00),
    }

    def __init__(self, api_key: str, model: str | None = None) -> None:
        self.api_key = api_key
        self.model = model or settings.PRIMARY_MODEL

    def _client(self):
        # Lazy import so the package is optional at install time.
        from openai import AsyncOpenAI  # type: ignore[import-not-found]

        return AsyncOpenAI(api_key=self.api_key)

    async def complete(
        self,
        messages: list[dict],
        *,
        max_tokens: int = 512,
        temperature: float = 0.4,
    ) -> LLMResult:
        client = self._client()
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,  # type: ignore[arg-type]
            max_tokens=max_tokens,
            temperature=temperature,
        )
        choice = response.choices[0].message
        content = (choice.content or "").strip()
        usage = response.usage
        tokens_input = getattr(usage, "prompt_tokens", 0) or 0
        tokens_output = getattr(usage, "completion_tokens", 0) or 0
        return LLMResult(
            content=content,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            cost_cents=self._cost_cents(tokens_input, tokens_output),
            model=self.model,
            raw=response,
        )

    def _cost_cents(self, tokens_in: int, tokens_out: int) -> int:
        prices = self._PRICING.get(self.model)
        if not prices:
            return 0
        in_per_million_usd, out_per_million_usd = prices
        usd = (
            tokens_in * in_per_million_usd / 1_000_000
            + tokens_out * out_per_million_usd / 1_000_000
        )
        # Round up to whole cents so we never under-charge.
        return max(0, int(round(usd * 100)))


def get_llm() -> LLMProvider:
    """Pick an LLM provider based on settings.

    Falls back to ``FakeLLM`` whenever the real provider is misconfigured or
    its package is missing, so the agent always has *something* to call.
    """
    if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        try:
            import openai  # noqa: F401  type: ignore[import-not-found]

            return OpenAILLM(api_key=settings.OPENAI_API_KEY)
        except ImportError:
            logger.warning(
                "LLM_PROVIDER=openai but the 'openai' package is not installed; "
                "falling back to FakeLLM."
            )
    return FakeLLM()


__all__ = ["LLMResult", "LLMProvider", "FakeLLM", "OpenAILLM", "get_llm"]
