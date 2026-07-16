"""Real-LLM integration test (ai/DECISIONS.md #32). The one test in this
suite that spends real Anthropic API credits — automatically skipped
unless ANTHROPIC_API_KEY is present in the environment, so a normal
`pytest` run (CI, or a machine with no key) never spends money by
surprise. Run deliberately: `pytest tests/test_real_llm_integration.py`
with the key set.

Exercises the one combination no other test does: the real Anthropic
model (tool selection is genuinely the model's own decision — hard
constraint #2, nothing scripted here) talking to the real MCP server over
real stdio. test_real_mcp_integration.py covers real-MCP + fake-model;
test_agent_loop_*.py covers fake-MCP + fake-model. This is real + real.
"""

from __future__ import annotations

import os

import pytest

from agent_loop import run_task
from config import ANTHROPIC_MODEL, MCP_SERVER_SCRIPT
from mcp_client import StdioMCPClient
from model_client import AnthropicModelClient
from schemas import FailureReason, GroundingStatus, TaskStatus
from system_prompt import load_system_prompt

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="requires a real ANTHROPIC_API_KEY — skipped by default, run deliberately",
)


async def test_real_model_answers_a_zero_certifications_lookup_honestly():
    """SUP-017 (E2 fixture) genuinely has zero certifications. The real
    model must call a real tool to find that out — it cannot know this from
    training data, since this dataset is fabricated for this project — and
    must report the empty result honestly rather than inventing one."""
    model = AnthropicModelClient(model=ANTHROPIC_MODEL)
    mcp = StdioMCPClient(MCP_SERVER_SCRIPT)

    trace = await run_task(
        task_id="real-llm-1",
        task_input="Does supplier SUP-017 have any certifications on file? If so, list them.",
        model_client=model,
        mcp_client=mcp,
        system_prompt=load_system_prompt(),
    )

    assert trace.status in (TaskStatus.COMPLETED, TaskStatus.COMPLETED_PARTIAL)
    assert trace.failure_reason is None
    assert len(trace.tool_calls) >= 1, "the real model must call a tool, not answer from training data"
    assert all(c.reasoning for c in trace.tool_calls), "reasoning must be present on every real tool call too"
    assert trace.final_answer
    assert trace.grounding_check is not None


async def test_real_model_reports_a_legitimate_empty_result_without_fabricating():
    """A quality-incidents query with no matching data (E1-style: a future
    since_date). The real model must report "no incidents found," not
    invent one — checked both in the answer text and via the grounding
    mechanical backstop (specs/agent-spec.md §17)."""
    model = AnthropicModelClient(model=ANTHROPIC_MODEL)
    mcp = StdioMCPClient(MCP_SERVER_SCRIPT)

    trace = await run_task(
        task_id="real-llm-2",
        task_input="Have there been any quality incidents recorded since the year 2099?",
        model_client=model,
        mcp_client=mcp,
        system_prompt=load_system_prompt(),
    )

    assert trace.status in (TaskStatus.COMPLETED, TaskStatus.COMPLETED_PARTIAL)
    assert trace.failure_reason is None
    assert len(trace.tool_calls) >= 1
    assert trace.final_answer
    assert trace.grounding_check is not None
    assert trace.grounding_check.status == GroundingStatus.PASSED, (
        f"real model appears to have referenced an ID never returned by any tool: "
        f"{trace.grounding_check.unrecognized_references}"
    )


async def test_real_model_never_leaks_a_raw_exception_on_a_real_run():
    """Not a failure-injection test (those are covered deterministically in
    test_agent_loop_failures.py) — just a sanity check that a real run
    against the real model and real server never ends in an unhandled
    exception reaching the caller (hard constraint #5)."""
    model = AnthropicModelClient(model=ANTHROPIC_MODEL)
    mcp = StdioMCPClient(MCP_SERVER_SCRIPT)

    trace = await run_task(
        task_id="real-llm-3",
        task_input="Which suppliers in Italy have a valid BRCGS certification?",
        model_client=model,
        mcp_client=mcp,
        system_prompt=load_system_prompt(),
    )

    assert trace.status != TaskStatus.FAILED or trace.failure_reason != FailureReason.INTERNAL_ERROR
