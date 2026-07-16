"""Happy path (CLAUDE.md §"Testing scenarios", specs/agent-spec.md §12):
"which dairy suppliers have an expired certification" — search_suppliers
(R1, no ID given) -> get_supplier_profile per each dairy supplier returned
(R6, multi-target, exercised here as two tool_use blocks in one turn) -> each
ID sourced from the search result (R4) -> answer only after all suppliers
checked (R3)."""

from agent_loop import run_task
from mcp_client import FakeMCPClient
from model_client import FakeModelClient, text_response, tool_call_response
from schemas import LimitHit, TaskStatus


def _search_suppliers(args: dict) -> dict:
    assert args.get("category") == "DAIRY"
    assert args.get("reasoning"), "reasoning must be present on every tool call"
    return {
        "results": [
            {"id": "SUP-001", "name": "Dairy Fresh Ltd", "country": "IT", "category": "DAIRY", "risk_rating": "LOW"},
            {"id": "SUP-002", "name": "Latteria Rossi", "country": "IT", "category": "DAIRY", "risk_rating": "MEDIUM"},
        ],
        "count": 2,
    }


def _get_supplier_profile(args: dict) -> dict:
    assert args.get("reasoning")
    sid = args["supplier_id"]
    if sid == "SUP-001":
        return {
            "supplier": {"id": "SUP-001", "name": "Dairy Fresh Ltd", "country": "IT", "category": "DAIRY", "risk_rating": "LOW"},
            "certifications": [
                {"id": "CERT-001", "standard": "BRCGS", "status": "EXPIRED", "expiry_date": "2025-01-01"}
            ],
        }
    if sid == "SUP-002":
        return {
            "supplier": {"id": "SUP-002", "name": "Latteria Rossi", "country": "IT", "category": "DAIRY", "risk_rating": "MEDIUM"},
            "certifications": [
                {"id": "CERT-002", "standard": "ISO22000", "status": "VALID", "expiry_date": "2027-01-01"}
            ],
        }
    raise AssertionError(f"unexpected supplier_id {sid}")


async def test_happy_path_multi_target_dairy_suppliers():
    mcp = FakeMCPClient(
        handlers={"search_suppliers": _search_suppliers, "get_supplier_profile": _get_supplier_profile}
    )
    model = FakeModelClient(
        script=[
            tool_call_response(
                [("search_suppliers", {"category": "DAIRY", "reasoning": "find dairy suppliers first, per R1"})],
                thinking="The task asks about dairy suppliers, so I need to search first.",
            ),
            tool_call_response(
                [
                    ("get_supplier_profile", {"supplier_id": "SUP-001", "reasoning": "check SUP-001's certifications"}),
                    ("get_supplier_profile", {"supplier_id": "SUP-002", "reasoning": "check SUP-002's certifications"}),
                ],
                thinking="Two dairy suppliers were found; per R6 I must check both, not just the first.",
            ),
            text_response(
                "SUP-001 (Dairy Fresh Ltd) has an expired BRCGS certification (CERT-001). "
                "SUP-002 (Latteria Rossi) has a valid ISO22000 certification (CERT-002), no expired ones."
            ),
        ]
    )

    trace = await run_task(
        task_id="t1",
        task_input="which dairy suppliers have an expired certification",
        model_client=model,
        mcp_client=mcp,
        system_prompt="test system prompt",
    )

    assert trace.status == TaskStatus.COMPLETED
    assert trace.limit_hit == LimitHit.NONE
    assert trace.failure_reason is None
    assert len(trace.tool_calls) == 3  # 1 search + 2 profile calls
    assert all(c.success for c in trace.tool_calls)
    assert all(c.reasoning for c in trace.tool_calls)  # reasoning always captured verbatim
    assert trace.tool_calls[0].tool_name == "search_suppliers"
    assert {trace.tool_calls[1].tool_name, trace.tool_calls[2].tool_name} == {"get_supplier_profile"}
    assert trace.tool_calls[1].thinking is not None  # extended-thinking captured per step
    assert "SUP-001" in trace.final_answer
    assert trace.grounding_check.status.value == "PASSED"  # both cited IDs came from real tool results
    assert trace.grounding_check.unrecognized_references == []
