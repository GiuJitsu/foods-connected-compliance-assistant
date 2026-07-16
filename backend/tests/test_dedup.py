"""R2/R5 backend dedup safety net (specs/agent-spec.md §5): a repeated
identical tool+input call within one task is served from cache instead of
re-invoked, and does not consume iteration budget."""

from agent_loop import run_task
from mcp_client import FakeMCPClient
from model_client import FakeModelClient, text_response, tool_call_response
from schemas import TaskStatus


async def test_identical_repeated_call_is_served_from_cache_not_reexecuted():
    call_count = {"n": 0}

    def _search(args: dict) -> dict:
        call_count["n"] += 1
        return {"results": [{"id": "SUP-001", "name": "X", "country": "IT", "category": "DAIRY", "risk_rating": "LOW"}], "count": 1}

    mcp = FakeMCPClient(handlers={"search_suppliers": _search})
    model = FakeModelClient(
        script=[
            tool_call_response([("search_suppliers", {"category": "DAIRY", "reasoning": "first search"})]),
            # Model (mis)behaves and repeats the identical domain input — only
            # `reasoning` differs, which must not count as a different call.
            tool_call_response([("search_suppliers", {"category": "DAIRY", "reasoning": "checking again just in case"})]),
            text_response("Found SUP-001, a dairy supplier."),
        ]
    )

    trace = await run_task(
        task_id="t7",
        task_input="find dairy suppliers",
        model_client=model,
        mcp_client=mcp,
        system_prompt="test system prompt",
    )

    assert call_count["n"] == 1  # the real MCP tool only ran once
    assert len(trace.tool_calls) == 2  # both attempts are still visible in the trace
    assert "cache" in trace.tool_calls[1].result_summary.lower()
    assert trace.tool_calls[1].latency_ms == 0
    assert trace.status == TaskStatus.COMPLETED
