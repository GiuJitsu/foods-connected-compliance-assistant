"""Grounding mechanical backstop (specs/agent-spec.md §17): unit tests on
grounding.py directly, plus one end-to-end test through the agent loop."""

from agent_loop import run_task
from grounding import compute_grounding_check, extract_id_tokens
from mcp_client import FakeMCPClient
from model_client import FakeModelClient, text_response, tool_call_response
from schemas import GroundingStatus


def test_extract_id_tokens_matches_all_four_id_conventions():
    text = "See SUP-001, SUP-TIMEOUT-01, CERT-042, SPEC-007 and INC-003 for details."
    assert extract_id_tokens(text) == {"SUP-001", "SUP-TIMEOUT-01", "CERT-042", "SPEC-007", "INC-003"}


def test_compute_grounding_check_flags_unreturned_id():
    tool_results = [{"results": [{"id": "SUP-001", "name": "X"}], "count": 1}]
    check = compute_grounding_check("SUP-001 is fine but SUP-999 was also mentioned.", tool_results)
    assert check.status == GroundingStatus.FLAGGED
    assert check.unrecognized_references == ["SUP-999"]


def test_compute_grounding_check_passes_when_every_id_traces_to_a_result():
    tool_results = [{"supplier": {"id": "SUP-001"}, "certifications": [{"id": "CERT-001", "supplier_id": "SUP-001"}]}]
    check = compute_grounding_check("SUP-001 has certification CERT-001.", tool_results)
    assert check.status == GroundingStatus.PASSED
    assert check.unrecognized_references == []


async def test_end_to_end_flagged_when_model_invents_an_id():
    mcp = FakeMCPClient(
        handlers={"search_suppliers": lambda args: {"results": [{"id": "SUP-001", "name": "X"}], "count": 1}}
    )
    model = FakeModelClient(
        script=[
            tool_call_response([("search_suppliers", {"reasoning": "look up suppliers"})]),
            # Hallucination: cites SUP-999, which was never in any tool result.
            text_response("SUP-001 and SUP-999 are both compliant."),
        ]
    )

    trace = await run_task(
        task_id="t8",
        task_input="check compliance",
        model_client=model,
        mcp_client=mcp,
        system_prompt="test system prompt",
    )

    assert trace.grounding_check.status == GroundingStatus.FLAGGED
    assert trace.grounding_check.unrecognized_references == ["SUP-999"]
    # grounding_check must never change task status (specs/agent-spec.md §17)
    assert trace.status.value in ("COMPLETED", "COMPLETED_PARTIAL")
