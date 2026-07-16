"""True end-to-end test (ai/DECISIONS.md #31): submit over the real HTTP
API and let the real background run_task() execute — unlike test_api.py,
_run_and_store is NOT stubbed here. Only the model is swapped for a
FakeModelClient (no API key needed); the MCP server is the real subprocess
over real stdio, same as test_real_mcp_integration.py.

Closes the one gap neither existing suite covers: test_api.py proves the
HTTP contract with the loop stubbed out, and test_agent_loop_*.py /
test_real_mcp_integration.py prove the loop works when called directly —
but nothing previously proved the whole stack wired together through the
actual FastAPI request/background-task/polling flow a real frontend uses.
"""

import time

import pytest
from fastapi.testclient import TestClient

import main
from model_client import FakeModelClient, text_response, tool_call_response


@pytest.fixture(autouse=True)
def _use_fake_model_real_everything_else(monkeypatch):
    model = FakeModelClient(
        script=[
            tool_call_response(
                [
                    (
                        "search_suppliers",
                        {
                            "country": "IT",
                            "category": "DAIRY",
                            "reasoning": "find Italian dairy suppliers, end-to-end HTTP test",
                        },
                    )
                ]
            ),
            text_response("There are Italian dairy suppliers in the dataset, per the search result above."),
        ]
    )
    monkeypatch.setattr(main, "_make_model_client", lambda: model)
    main._TASKS.clear()
    yield
    main._TASKS.clear()


def test_submission_to_result_round_trip_over_real_http_and_real_mcp_server():
    with TestClient(main.app) as client:
        submit = client.post("/api/tasks", json={"task": "which dairy suppliers are in Italy"})
        assert submit.status_code == 200
        assert submit.json()["status"] == "IN_PROGRESS"
        task_id = submit.json()["task_id"]

        deadline = time.monotonic() + 20
        trace = None
        while time.monotonic() < deadline:
            got = client.get(f"/api/tasks/{task_id}")
            assert got.status_code == 200
            body = got.json()
            if body["status"] != "IN_PROGRESS":
                trace = body
                break
            time.sleep(0.2)

        assert trace is not None, "task never left IN_PROGRESS within the deadline"
        assert trace["status"] == "COMPLETED"
        assert trace["limit_hit"] == "NONE"
        assert len(trace["tool_calls"]) == 1
        call = trace["tool_calls"][0]
        assert call["tool_name"] == "search_suppliers"
        assert call["success"] is True
        assert "result(s) found" in call["result_summary"]
        assert call["reasoning"]
        assert trace["final_answer"]
        assert trace["grounding_check"]["status"] == "PASSED"
