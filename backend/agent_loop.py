"""The bounded product agent loop (specs/agent-spec.md §3, §9; CLAUDE.md hard
constraint #4).

Orchestrates: MCP-reachability check at task start -> repeated model turns,
each free to call zero or more of the 5 MCP tools (hard constraint #2 — this
module never chooses a tool, only executes what the model asks for) -> trace
recording matching specs/mcp-integration-spec.md §10 exactly -> status/
limit_hit/failure_reason determination -> the grounding mechanical backstop
(specs/agent-spec.md §17).

Every "who decides what" line below traces to specs/agent-spec.md §17's
LLM-vs-Python responsibility table:
- Which tool, what order, tool argument values, reasoning text: the model.
- reasoning presence, iteration cap, timeouts, status, trace recording,
  MCP-unreachable check, grounding: this module (hard-enforced).
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Optional

from config import ITERATION_CAP, PER_CALL_TIMEOUT_S, TOTAL_TASK_TIMEOUT_S
from grounding import compute_grounding_check
from mcp_client import MCPClient, MCPToolDef, MCPUnreachableError
from model_client import ModelAPIError, ModelClient, ToolUseBlock
from schemas import (
    FailureReason,
    LimitHit,
    TaskStatus,
    TaskTrace,
    ToolCallError,
    ToolCallTrace,
    ToolErrorType,
)

_WRAP_UP_NOTICE = (
    "You have reached your tool-call budget (8 calls). Do not call any more tools. "
    "Give your best final answer now using only the information already gathered, "
    "and state explicitly that the task may be incomplete."
)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_input(tool_input: dict) -> str:
    """Input with `reasoning` excluded, canonicalized for dedup comparison
    (R2/R5, specs/agent-spec.md §5 — reasoning text differing doesn't make two
    calls materially different)."""
    without_reasoning = {k: v for k, v in tool_input.items() if k != "reasoning"}
    return json.dumps(without_reasoning, sort_keys=True, default=str)


def _classify_result(content: dict) -> tuple[bool, Optional[ToolCallError]]:
    if not isinstance(content, dict) or "error" not in content:
        return True, None
    raw_type = content.get("error")
    try:
        etype = ToolErrorType(raw_type)
    except ValueError:
        etype = ToolErrorType.SERVER_ERROR
    message = content.get("message") or json.dumps(content)
    return False, ToolCallError(type=etype, message=message)


def _summarize_result(tool_name: str, content: dict) -> str:
    if isinstance(content, dict) and "error" in content:
        return f"Error: {content.get('message', content.get('error'))}"
    if isinstance(content, dict) and "results" in content and "count" in content:
        return f"{content['count']} result(s) found"
    if tool_name == "get_supplier_profile" and isinstance(content, dict) and "supplier" in content:
        n_certs = len(content.get("certifications", []))
        name = content["supplier"].get("name", "?")
        return f"Supplier '{name}' — {n_certs} certification(s)"
    if tool_name == "check_allergen_conflicts" and isinstance(content, dict):
        return f"has_conflict={content.get('has_conflict')}, conflicts={content.get('conflicts')}"
    return json.dumps(content)[:200]


def _synthesize_partial_answer(trace: list[ToolCallTrace]) -> str:
    """Deterministic fallback answer text used only when the loop is cut off
    (cap/timeout) with no model-produced final text to fall back on —
    specs/agent-spec.md §3: "never truncate silently". Not a model call: by
    construction this path only runs when the total-task time budget is
    already exhausted, so issuing one more model call isn't safe to rely on."""
    if not trace:
        return "The task did not complete within the available budget before any tool call finished."
    ok = [t for t in trace if t.success]
    failed = [t for t in trace if not t.success]
    lines = [
        f"The task did not complete within the available budget. "
        f"{len(ok)} of {len(trace)} tool call(s) succeeded before the budget was reached."
    ]
    for t in trace:
        state = "OK" if t.success else f"FAILED ({t.error.type.value if t.error else '?'})"
        lines.append(f"- {t.tool_name}({t.input}) -> {state}: {t.result_summary}")
    if failed:
        lines.append("This answer is incomplete; the failed/unattempted calls above were not resolved.")
    return "\n".join(lines)


def _anthropic_tool_defs(tools: list[MCPToolDef]) -> list[dict]:
    return [{"name": t.name, "description": t.description, "input_schema": t.input_schema} for t in tools]


def _skipped_tool_result_block(tool_use_id: str, reason: str) -> dict:
    return {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": json.dumps({"error": "SERVER_ERROR", "message": f"not executed: {reason}"}),
    }


async def run_task(
    *,
    task_id: str,
    task_input: str,
    model_client: ModelClient,
    mcp_client: MCPClient,
    system_prompt: str,
) -> TaskTrace:
    start = time.monotonic()

    # --- Step 1: MCP reachability check at task start (specs/agent-spec.md §9 #1) ---
    try:
        await mcp_client.connect()
        tool_defs = await mcp_client.list_tools()
    except MCPUnreachableError:
        return TaskTrace(
            task_id=task_id,
            task_input=task_input,
            status=TaskStatus.FAILED,
            limit_hit=LimitHit.NONE,
            tool_calls=[],
            final_answer=None,
            failure_reason=FailureReason.MCP_UNREACHABLE,
            model=model_client.model_name,
            total_duration_ms=int((time.monotonic() - start) * 1000),
            grounding_check=None,
        )

    anthropic_tools = _anthropic_tool_defs(tool_defs)
    messages: list[dict] = [{"role": "user", "content": task_input}]
    trace: list[ToolCallTrace] = []
    tool_results_raw: list[dict] = []
    dedup_cache: dict[tuple[str, str], dict] = {}
    iteration_count = 0
    limit_hit = LimitHit.NONE
    final_answer: Optional[str] = None

    try:
        while True:
            elapsed = time.monotonic() - start
            remaining = TOTAL_TASK_TIMEOUT_S - elapsed
            if remaining <= 0:
                limit_hit = LimitHit.TIMEOUT
                break

            force_wrap_up = iteration_count >= ITERATION_CAP
            call_messages = messages
            if force_wrap_up:
                call_messages = messages + [{"role": "user", "content": _WRAP_UP_NOTICE}]

            try:
                response = await asyncio.wait_for(
                    model_client.generate(system=system_prompt, messages=call_messages, tools=anthropic_tools),
                    timeout=remaining,
                )
            except asyncio.TimeoutError:
                limit_hit = LimitHit.TIMEOUT
                break
            except ModelAPIError:
                await mcp_client.close()
                return TaskTrace(
                    task_id=task_id,
                    task_input=task_input,
                    status=TaskStatus.FAILED,
                    limit_hit=LimitHit.NONE,
                    tool_calls=trace,
                    final_answer=None,
                    failure_reason=FailureReason.MODEL_API_FAILURE,
                    model=model_client.model_name,
                    total_duration_ms=int((time.monotonic() - start) * 1000),
                    grounding_check=None,
                )

            if force_wrap_up or not response.tool_uses:
                final_answer = response.text or _synthesize_partial_answer(trace)
                if force_wrap_up:
                    limit_hit = LimitHit.ITERATION_CAP
                break

            # Model chose to call one or more tools this turn.
            messages.append({"role": "assistant", "content": response.raw_assistant_blocks})
            tool_result_blocks: list[dict] = []

            for tu in response.tool_uses:
                elapsed = time.monotonic() - start
                remaining = TOTAL_TASK_TIMEOUT_S - elapsed
                if remaining <= 0:
                    limit_hit = LimitHit.TIMEOUT
                    tool_result_blocks.append(_skipped_tool_result_block(tu.id, "total task timeout reached"))
                    continue
                if iteration_count >= ITERATION_CAP:
                    limit_hit = LimitHit.ITERATION_CAP
                    tool_result_blocks.append(_skipped_tool_result_block(tu.id, "iteration cap reached"))
                    continue

                dedup_key = (tu.name, _canonical_input(tu.input))
                reasoning = str(tu.input.get("reasoning", ""))

                if dedup_key in dedup_cache:
                    # R2/R5 backend safety net (specs/agent-spec.md §5): serve
                    # the cached result instead of re-invoking the tool; does
                    # not consume iteration budget since nothing new ran.
                    cached_content = dedup_cache[dedup_key]
                    success, error = _classify_result(cached_content)
                    trace.append(
                        ToolCallTrace(
                            timestamp=_iso_now(),
                            tool_name=tu.name,
                            input=tu.input,
                            reasoning=reasoning,
                            thinking=response.thinking,
                            result_summary=f"[duplicate call served from cache] {_summarize_result(tu.name, cached_content)}",
                            success=success,
                            error=error,
                            latency_ms=0,
                        )
                    )
                    tool_result_blocks.append(
                        {"type": "tool_result", "tool_use_id": tu.id, "content": json.dumps(cached_content)}
                    )
                    continue

                iteration_count += 1
                call_started = time.monotonic()
                per_call_budget = min(PER_CALL_TIMEOUT_S, remaining)
                try:
                    result = await asyncio.wait_for(mcp_client.call_tool(tu.name, tu.input), timeout=per_call_budget)
                    content = result.content
                except asyncio.TimeoutError:
                    content = {"error": "TIMEOUT", "message": f"tool call exceeded {PER_CALL_TIMEOUT_S}s"}
                except Exception as exc:  # transport-level fault mid-call, not a tool-level error
                    content = {"error": "SERVER_ERROR", "message": str(exc)}

                latency_ms = int((time.monotonic() - call_started) * 1000)
                success, error = _classify_result(content)
                dedup_cache[dedup_key] = content
                tool_results_raw.append(content)

                trace.append(
                    ToolCallTrace(
                        timestamp=_iso_now(),
                        tool_name=tu.name,
                        input=tu.input,
                        reasoning=reasoning,
                        thinking=response.thinking,
                        result_summary=_summarize_result(tu.name, content),
                        success=success,
                        error=error,
                        latency_ms=latency_ms,
                    )
                )
                tool_result_blocks.append(
                    {"type": "tool_result", "tool_use_id": tu.id, "content": json.dumps(content)}
                )

            messages.append({"role": "user", "content": tool_result_blocks})

            if limit_hit != LimitHit.NONE:
                # A skip happened inside this batch (cap or timeout hit
                # mid-batch) — go straight to a wrap-up attempt next loop
                # iteration rather than starting a fresh, doomed-to-be-skipped
                # tool round. The top-of-loop checks (remaining<=0 /
                # force_wrap_up) handle producing the final answer.
                continue
    except Exception:
        # ai/build-loop-fix-log.md gap #3: an unexpected internal fault here
        # is a genuine backend bug, not a documented model/MCP failure mode —
        # now has its own bucket (FailureReason.INTERNAL_ERROR) rather than
        # being folded into MODEL_API_FAILURE, which would mislead a reviewer
        # into blaming the model/API for our bug. Hard constraint #5
        # ("failures must produce a meaningful state, never a hang or a raw
        # stack trace") still applies: this is still a clean TaskTrace, not a
        # leaked exception.
        return TaskTrace(
            task_id=task_id,
            task_input=task_input,
            status=TaskStatus.FAILED,
            limit_hit=LimitHit.NONE,
            tool_calls=trace,
            final_answer=None,
            failure_reason=FailureReason.INTERNAL_ERROR,
            model=model_client.model_name,
            total_duration_ms=int((time.monotonic() - start) * 1000),
            grounding_check=None,
        )
    finally:
        await mcp_client.close()

    if final_answer is None:
        final_answer = _synthesize_partial_answer(trace)

    any_failed = any(not t.success for t in trace)
    status = TaskStatus.COMPLETED_PARTIAL if (limit_hit != LimitHit.NONE or any_failed) else TaskStatus.COMPLETED

    grounding_check = compute_grounding_check(final_answer, tool_results_raw)

    return TaskTrace(
        task_id=task_id,
        task_input=task_input,
        status=status,
        limit_hit=limit_hit,
        tool_calls=trace,
        final_answer=final_answer,
        failure_reason=None,
        model=model_client.model_name,
        total_duration_ms=int((time.monotonic() - start) * 1000),
        grounding_check=grounding_check,
    )
