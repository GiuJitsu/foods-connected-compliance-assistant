"""End-to-end wiring check against the REAL mcp-server/server.py (spawned as
an actual stdio subprocess), combined with a FakeModelClient — the exact
combination the environment notes call out as the safe way to "mechanically
verify the loop works" without spending on the real Anthropic API. This is
the one test that proves backend/mcp_client.py's StdioMCPClient actually
speaks MCP correctly to the already-verified server, not just to FakeMCPClient.
"""

from config import MCP_SERVER_SCRIPT
from agent_loop import run_task
from mcp_client import StdioMCPClient
from model_client import FakeModelClient, text_response, tool_call_response
from schemas import LimitHit, TaskStatus, ToolErrorType


async def test_real_server_search_suppliers_round_trip():
    model = FakeModelClient(
        script=[
            tool_call_response(
                [("search_suppliers", {"country": "IT", "category": "DAIRY", "reasoning": "find Italian dairy suppliers"})]
            ),
            text_response("placeholder — overwritten below once we see the real result"),
        ]
    )

    mcp = StdioMCPClient(MCP_SERVER_SCRIPT)
    trace = await run_task(
        task_id="t9",
        task_input="which dairy suppliers are in Italy",
        model_client=model,
        mcp_client=mcp,
        system_prompt="test system prompt",
    )

    assert trace.status == TaskStatus.COMPLETED
    assert len(trace.tool_calls) == 1
    call = trace.tool_calls[0]
    assert call.success is True
    assert call.tool_name == "search_suppliers"
    # mockdata/suppliers.json has >=3 Italian dairy suppliers (SUP-001..003) —
    # proves real data actually round-tripped through the real MCP server.
    assert "result(s) found" in call.result_summary


async def test_real_server_rejects_missing_reasoning_as_validation_error():
    """Structural enforcement (specs/agent-spec.md §6): a blank/missing
    `reasoning` must fail with VALIDATION_ERROR from the real server, not be
    silently accepted. Exercised here by asking the FakeModelClient to send
    empty reasoning."""
    model = FakeModelClient(
        script=[
            tool_call_response([("search_suppliers", {"country": "IT", "reasoning": ""})]),
            text_response("The previous call failed validation; I cannot proceed further."),
        ]
    )

    mcp = StdioMCPClient(MCP_SERVER_SCRIPT)
    trace = await run_task(
        task_id="t10",
        task_input="which suppliers are in Italy",
        model_client=model,
        mcp_client=mcp,
        system_prompt="test system prompt",
    )

    assert len(trace.tool_calls) == 1
    assert trace.tool_calls[0].success is False
    assert trace.tool_calls[0].error.type == ToolErrorType.VALIDATION_ERROR
    assert trace.status == TaskStatus.COMPLETED_PARTIAL
    assert trace.limit_hit == LimitHit.NONE


async def test_real_server_unknown_supplier_id_is_not_found():
    model = FakeModelClient(
        script=[
            tool_call_response(
                [("get_supplier_profile", {"supplier_id": "SUP-DOES-NOT-EXIST", "reasoning": "look up this supplier"})]
            ),
            text_response("That supplier does not exist in the dataset."),
        ]
    )

    mcp = StdioMCPClient(MCP_SERVER_SCRIPT)
    trace = await run_task(
        task_id="t11",
        task_input="check SUP-DOES-NOT-EXIST",
        model_client=model,
        mcp_client=mcp,
        system_prompt="test system prompt",
    )

    assert trace.tool_calls[0].success is False
    assert trace.tool_calls[0].error.type == ToolErrorType.NOT_FOUND
    assert trace.status == TaskStatus.COMPLETED_PARTIAL
