"""FastAPI endpoint tests (backend/main.py). The real task-running path
(_run_and_store) is monkeypatched to a no-op recorder here — it already has
full coverage via tests/test_agent_loop_*.py and test_real_mcp_integration.py
against the real MCP server; these tests are about the HTTP contract itself
(status codes, immediate-IN_PROGRESS response per AC2, 404 for unknown ids),
not the agent loop's internal behaviour."""

import pytest
from fastapi.testclient import TestClient

import main
from schemas import LimitHit, TaskStatus, TaskTrace


@pytest.fixture(autouse=True)
def _stub_background_run(monkeypatch):
    async def _fake_run_and_store(task_id: str, task_input: str) -> None:
        main._TASKS[task_id] = TaskTrace(
            task_id=task_id,
            task_input=task_input,
            status=TaskStatus.COMPLETED,
            limit_hit=LimitHit.NONE,
            tool_calls=[],
            final_answer="stubbed answer",
            model="fake-model",
            total_duration_ms=1,
            grounding_check=None,
        )

    monkeypatch.setattr(main, "_run_and_store", _fake_run_and_store)
    main._TASKS.clear()
    yield
    main._TASKS.clear()


@pytest.fixture
def client():
    return TestClient(main.app)


def test_submit_task_returns_in_progress_immediately(client):
    resp = client.post("/api/tasks", json={"task": "which suppliers are in Italy"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "IN_PROGRESS"
    assert "task_id" in body


def test_submit_empty_task_is_rejected(client):
    resp = client.post("/api/tasks", json={"task": "   "})
    assert resp.status_code == 422


def test_get_unknown_task_is_404(client):
    resp = client.get("/api/tasks/does-not-exist")
    assert resp.status_code == 404


def test_get_task_after_submit_returns_trace_shape(client):
    submit = client.post("/api/tasks", json={"task": "check SUP-001"})
    task_id = submit.json()["task_id"]
    got = client.get(f"/api/tasks/{task_id}")
    assert got.status_code == 200
    body = got.json()
    assert body["task_id"] == task_id
    assert "tool_calls" in body
    assert "status" in body


def test_info_endpoint_exposes_static_loop_limits(client):
    resp = client.get("/api/info")
    assert resp.status_code == 200
    body = resp.json()
    assert body["iteration_cap"] == 8
    assert body["per_call_timeout_s"] == 10
    assert body["total_timeout_s"] == 60
    assert "model" in body
