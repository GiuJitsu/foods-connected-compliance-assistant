"""Loop-bound enforcement (CLAUDE.md hard constraint #4; specs/agent-spec.md
§3): iteration cap and total timeout, both required to end the task with a
best-effort partial answer, never silently."""

import agent_loop as al
from agent_loop import run_task
from mcp_client import FakeMCPClient
from model_client import FakeModelClient, text_response, tool_call_response
from schemas import LimitHit, TaskStatus


async def test_iteration_cap_stops_the_loop_and_forces_wrap_up():
    call_count = {"n": 0}

    def _search(args: dict) -> dict:
        call_count["n"] += 1
        return {"results": [], "count": 0}

    mcp = FakeMCPClient(handlers={"search_suppliers": _search})

    # 8 distinct tool-call turns (each with a different query so R2 dedup
    # never intercepts them), then a 9th turn that must be the forced
    # wrap-up call regardless of what it contains.
    script = [
        tool_call_response([("search_suppliers", {"query": f"q{i}", "reasoning": f"lookup {i}"})]) for i in range(8)
    ]
    script.append(text_response("Reached the tool-call budget; here is what I found so far: nothing matched."))
    model = FakeModelClient(script=script)

    trace = await run_task(
        task_id="t5",
        task_input="do 9 separate searches",
        model_client=model,
        mcp_client=mcp,
        system_prompt="test system prompt",
    )

    assert call_count["n"] == 8  # the 9th tool_use, if the model had tried one, would never execute
    assert len(trace.tool_calls) == 8
    assert trace.limit_hit == LimitHit.ITERATION_CAP
    assert trace.status == TaskStatus.COMPLETED_PARTIAL
    assert trace.final_answer is not None


async def test_total_timeout_ends_task_with_partial_answer_no_hang():
    mcp = FakeMCPClient(handlers={})
    model = FakeModelClient(script=[text_response("should never be reached")])

    orig_timeout = al.TOTAL_TASK_TIMEOUT_S
    al.TOTAL_TASK_TIMEOUT_S = 0  # force the very first budget check to fail immediately
    try:
        trace = await run_task(
            task_id="t6",
            task_input="anything",
            model_client=model,
            mcp_client=mcp,
            system_prompt="test system prompt",
        )
    finally:
        al.TOTAL_TASK_TIMEOUT_S = orig_timeout

    assert trace.limit_hit == LimitHit.TIMEOUT
    assert trace.status == TaskStatus.COMPLETED_PARTIAL
    assert trace.final_answer is not None  # never silently truncated
    assert model.calls == []  # budget was already exhausted before any model call
