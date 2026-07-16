"""Model client abstraction — swappable/mockable per the brief's own testing
guidance (CLAUDE.md "Tech stack": "agent loop against a fake model and fake
tool set called out as the natural target").

`ModelClient` is the interface agent_loop.py depends on. Two implementations:
- `AnthropicModelClient`: wraps the real Anthropic SDK, extended thinking
  enabled (specs/agent-spec.md §10, LOCKED). Never invoked in this build
  session (no API key configured, spending real credits isn't this agent's
  call to make) — written so it's ready to run once a key is provided, but
  mechanically verified only via FakeModelClient.
- `FakeModelClient`: scripted canned responses, used by tests to exercise the
  loop deterministically (loop-bound enforcement, failure scenarios, result
  handling) with no network/spend, per CLAUDE.md "Testing requirements".
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class ToolUseBlock:
    id: str
    name: str
    input: dict


@dataclass
class ModelResponse:
    """Normalized shape of one model turn, independent of the Anthropic SDK's
    own response object — the agent loop only ever depends on this shape, not
    on `anthropic` types directly, which is what keeps FakeModelClient a
    drop-in replacement with zero SDK dependency."""

    text: Optional[str]  # final/assistant text, if any, for this turn
    tool_uses: list[ToolUseBlock] = field(default_factory=list)
    thinking: Optional[str] = None  # raw extended-thinking content, if produced
    stop_reason: Optional[str] = None
    raw_assistant_blocks: list[dict] = field(default_factory=list)
    """The blocks to append back onto the conversation as the assistant turn,
    in Anthropic content-block shape (thinking/text/tool_use) — needed so the
    next turn's request replays the assistant's own tool_use blocks verbatim,
    which the Anthropic API requires for multi-turn tool use."""


class ModelAPIError(Exception):
    """Raised by a ModelClient when the underlying model/API call fails.
    Caught by agent_loop.py and mapped to status=FAILED,
    failure_reason=MODEL_API_FAILURE (specs/agent-spec.md §9 #3) — never
    surfaced as a raw stack trace to the caller."""


class ModelClient(ABC):
    @abstractmethod
    async def generate(
        self,
        *,
        system: str,
        messages: list[dict],
        tools: list[dict],
    ) -> ModelResponse:
        """One model turn. `messages` is the running conversation in Anthropic
        message-content-block shape. Raises ModelAPIError on any failure."""
        raise NotImplementedError

    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError


class AnthropicModelClient(ModelClient):
    """Real Anthropic API client. Not exercised in this build session (no
    ANTHROPIC_API_KEY configured here, and spending real credits is not this
    agent's call to make) — structured so it's the only piece that needs an
    API key to work, everything else in backend/ is provider-agnostic."""

    def __init__(
        self,
        *,
        model: str,
        api_key: Optional[str] = None,
        thinking_enabled: bool = True,
        thinking_budget_tokens: int = 1024,
        max_tokens: int = 2048,
    ) -> None:
        self._model = model
        self._api_key = api_key  # if None, the SDK reads ANTHROPIC_API_KEY from env itself
        self._thinking_enabled = thinking_enabled
        self._thinking_budget_tokens = thinking_budget_tokens
        self._max_tokens = max_tokens
        self._client = None  # lazily constructed — see _get_client

    @property
    def model_name(self) -> str:
        return self._model

    def _get_client(self):
        if self._client is None:
            import anthropic  # deferred import: keeps this module importable

            self._client = anthropic.AsyncAnthropic(api_key=self._api_key)
        return self._client

    async def generate(self, *, system: str, messages: list[dict], tools: list[dict]) -> ModelResponse:
        import anthropic

        client = self._get_client()
        kwargs: dict[str, Any] = dict(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            messages=messages,
            tools=tools,
        )
        if self._thinking_enabled:
            kwargs["thinking"] = {"type": "enabled", "budget_tokens": self._thinking_budget_tokens}
            # Extended thinking requires temperature 1 (Anthropic API constraint).
            kwargs["temperature"] = 1
        try:
            resp = await client.messages.create(**kwargs)
        except anthropic.APIError as exc:  # covers auth/rate-limit/server errors alike
            raise ModelAPIError(str(exc)) from exc
        except Exception as exc:  # network errors, timeouts, etc.
            raise ModelAPIError(str(exc)) from exc

        text_parts: list[str] = []
        tool_uses: list[ToolUseBlock] = []
        thinking_text: Optional[str] = None
        raw_blocks: list[dict] = []

        for block in resp.content:
            if block.type == "text":
                text_parts.append(block.text)
                raw_blocks.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                tool_uses.append(ToolUseBlock(id=block.id, name=block.name, input=block.input))
                raw_blocks.append({"type": "tool_use", "id": block.id, "name": block.name, "input": block.input})
            elif block.type == "thinking":
                thinking_text = getattr(block, "thinking", None)
                raw_blocks.append(
                    {"type": "thinking", "thinking": block.thinking, "signature": getattr(block, "signature", "")}
                )
            elif block.type == "redacted_thinking":
                raw_blocks.append({"type": "redacted_thinking", "data": getattr(block, "data", "")})

        return ModelResponse(
            text="\n".join(text_parts) if text_parts else None,
            tool_uses=tool_uses,
            thinking=thinking_text,
            stop_reason=resp.stop_reason,
            raw_assistant_blocks=raw_blocks,
        )


class FakeModelClient(ModelClient):
    """Deterministic, scripted model for tests. `script` is a list of factory
    callables, one per turn, each taking the running `messages` list and
    returning a ModelResponse for that turn. Using callables (not static
    responses) lets a test assert on what the loop sent back (e.g. that a
    tool_result was appended correctly) before deciding the next canned
    response.

    Raising `ModelAPIError` from a script step simulates a model/API failure
    (specs/agent-spec.md §9 #3) for the model-failure test scenario.
    """

    def __init__(self, script: list[Callable[[list[dict]], ModelResponse]], model_name: str = "fake-model-1"):
        self._script = script
        self._call_index = 0
        self._model_name = model_name
        self.calls: list[list[dict]] = []  # recorded for test assertions

    @property
    def model_name(self) -> str:
        return self._model_name

    async def generate(self, *, system: str, messages: list[dict], tools: list[dict]) -> ModelResponse:
        self.calls.append(messages)
        if self._call_index >= len(self._script):
            raise AssertionError(
                f"FakeModelClient script exhausted after {self._call_index} calls — "
                "test script is shorter than the loop actually ran."
            )
        step = self._script[self._call_index]
        self._call_index += 1
        return step(messages)


def text_response(text: str, thinking: Optional[str] = None) -> Callable[[list[dict]], ModelResponse]:
    """Convenience factory: a scripted turn that ends the loop with plain text."""

    def _factory(_messages: list[dict]) -> ModelResponse:
        blocks: list[dict] = []
        if thinking:
            blocks.append({"type": "thinking", "thinking": thinking, "signature": ""})
        blocks.append({"type": "text", "text": text})
        return ModelResponse(text=text, tool_uses=[], thinking=thinking, stop_reason="end_turn", raw_assistant_blocks=blocks)

    return _factory


def tool_call_response(
    calls: list[tuple[str, dict]], thinking: Optional[str] = None
) -> Callable[[list[dict]], ModelResponse]:
    """Convenience factory: a scripted turn that issues one or more tool
    calls. `calls` is a list of (tool_name, input_dict) pairs; tool_use ids
    are auto-generated and stable within the turn."""

    def _factory(_messages: list[dict]) -> ModelResponse:
        tool_uses = [ToolUseBlock(id=f"toolu_{i}", name=name, input=inp) for i, (name, inp) in enumerate(calls)]
        blocks: list[dict] = []
        if thinking:
            blocks.append({"type": "thinking", "thinking": thinking, "signature": ""})
        for tu in tool_uses:
            blocks.append({"type": "tool_use", "id": tu.id, "name": tu.name, "input": tu.input})
        return ModelResponse(
            text=None, tool_uses=tool_uses, thinking=thinking, stop_reason="tool_use", raw_assistant_blocks=blocks
        )

    return _factory


def raise_api_error(message: str = "simulated model/API failure") -> Callable[[list[dict]], ModelResponse]:
    def _factory(_messages: list[dict]) -> ModelResponse:
        raise ModelAPIError(message)

    return _factory
