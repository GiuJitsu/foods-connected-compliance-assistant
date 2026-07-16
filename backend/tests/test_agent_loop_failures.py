"""The 3 required failure scenarios (CLAUDE.md §"Testing scenarios"):
1. MCP server unreachable — harness-level fault, not data-dependent.
2. Tool call errors mid-task — data-dependent (SUP-TIMEOUT-01-style fixture).
3. Model/API failure — harness-level fault, not data-dependent.
"""

import asyncio

from agent_loop import run_task
from mcp_client import FakeMCPClient
from model_client import FakeModelClient, raise_api_error, text_response, tool_call_response
from schemas import FailureReason, LimitHit, TaskStatus, ToolErrorType


async def test_mcp_server_unreachable_at_task_start():
    mcp = FakeMCPClient(handlers={}, refuses_to_connect=True)
    model = FakeModelClient(script=[])  # must never be called — loop must not attempt at all

    trace = await run_task(
        task_id="t2",
        task_input="anything",
        model_client=model,
        mcp_client=mcp,
        system_prompt="test system prompt",
    )

    assert trace.status == TaskStatus.FAILED
    assert trace.failure_reason == FailureReason.MCP_UNREACHABLE
    assert trace.tool_calls == []
    assert trace.final_answer is None
    assert model.calls == []  # loop never attempted, per specs/agent-spec.md §9 #1


async def test_tool_call_error_mid_task_sets_completed_partial():
    """Mirrors the SUP-TIMEOUT-01 fixture: get_supplier_profile hangs past
    the 10s per-call timeout. Asserts the timeout is caught, logged with
    error.type == TIMEOUT, and the task still concludes as
    COMPLETED_PARTIAL with limit_hit == NONE (specs/agent-spec.md §9 #2 —
    distinct from an iteration-cap/timeout-triggered partial)."""

    async def _slow_profile(args: dict):
        await asyncio.sleep(999)  # asyncio.wait_for in agent_loop will cancel this well before 999s
        return {"supplier": {}, "certifications": []}

    mcp = FakeMCPClient(handlers={"get_supplier_profile": _slow_profile})
    model = FakeModelClient(
        script=[
            tool_call_response(
                [("get_supplier_profile", {"supplier_id": "SUP-TIMEOUT-01", "reasoning": "check this supplier"})]
            ),
            text_response(
                "I could not retrieve SUP-TIMEOUT-01's profile — the call timed out. No other information available."
            ),
        ]
    )

    import agent_loop as al

    # keep the test fast: shrink the per-call timeout instead of waiting 10s
    orig_timeout = al.PER_CALL_TIMEOUT_S
    al.PER_CALL_TIMEOUT_S = 0.05
    try:
        trace = await run_task(
            task_id="t3",
            task_input="check SUP-TIMEOUT-01's certifications",
            model_client=model,
            mcp_client=mcp,
            system_prompt="test system prompt",
        )
    finally:
        al.PER_CALL_TIMEOUT_S = orig_timeout

    assert trace.status == TaskStatus.COMPLETED_PARTIAL
    assert trace.limit_hit == LimitHit.NONE  # tool error, not a cap/timeout truncation
    assert len(trace.tool_calls) == 1
    assert trace.tool_calls[0].success is False
    assert trace.tool_calls[0].error.type == ToolErrorType.TIMEOUT
    assert trace.final_answer is not None


async def test_model_api_failure_mid_task():
    mcp = FakeMCPClient(handlers={})
    model = FakeModelClient(script=[raise_api_error("simulated Anthropic API outage")])

    trace = await run_task(
        task_id="t4",
        task_input="anything",
        model_client=model,
        mcp_client=mcp,
        system_prompt="test system prompt",
    )

    assert trace.status == TaskStatus.FAILED
    assert trace.failure_reason == FailureReason.MODEL_API_FAILURE
    assert trace.final_answer is None
    # no raw stack trace anywhere in the returned object (hard constraint #5)
    assert "Traceback" not in repr(trace)
