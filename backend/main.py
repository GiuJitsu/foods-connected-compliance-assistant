"""FastAPI backend for the Compliance Assistant product agent.

Endpoint contract chosen here (not specified by any of the read specs — see
the build report's "Questions / clarifications" section):

  POST /api/tasks         -> {task_id, status: IN_PROGRESS} immediately;
                              the agent loop runs in a background asyncio
                              task so the caller gets a response before any
                              tool call resolves (AC2's requirement).
  GET  /api/tasks/{id}     -> the current TaskTrace for that task (poll this
                              until status is COMPLETED / COMPLETED_PARTIAL /
                              FAILED) — this *is* the "view raw trace JSON"
                              object (CLAUDE.md §"Frontend transparency
                              requirements" #8).
  GET  /api/info           -> the static "how this agent works" info panel
                              data (AC12): model name, tool catalog, loop
                              limits.

CORS is enabled for local frontend dev (Vite default port) — a deployment
necessity, not a spec requirement.
"""

from __future__ import annotations

import asyncio
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agent_loop import run_task
from config import (
    ANTHROPIC_MODEL,
    CORS_ALLOW_ORIGINS,
    EXTENDED_THINKING_BUDGET_TOKENS,
    EXTENDED_THINKING_ENABLED,
    ITERATION_CAP,
    MCP_SERVER_SCRIPT,
    PER_CALL_TIMEOUT_S,
    TOTAL_TASK_TIMEOUT_S,
)
from mcp_client import MCPUnreachableError, StdioMCPClient
from model_client import AnthropicModelClient
from schemas import (
    AgentInfo,
    LimitHit,
    TaskStatus,
    TaskSubmitRequest,
    TaskSubmitResponse,
    TaskTrace,
    ToolCatalogEntry,
)
from system_prompt import load_system_prompt

@asynccontextmanager
async def _lifespan(_app: FastAPI):
    await _load_tool_catalog()
    yield


app = FastAPI(title="Compliance Assistant Backend", lifespan=_lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory task store — fine for a local single-process demo (no persistence
# requirement anywhere in the read specs). Keyed by task_id.
_TASKS: dict[str, TaskTrace] = {}

# Tool catalog cached at startup for the static info panel (AC12) — fetched
# once via a dedicated MCP connection, not re-fetched per request, matching
# "costs nothing at runtime" (CLAUDE.md §"Frontend transparency requirements" #7).
_TOOL_CATALOG: list[ToolCatalogEntry] = []


def _make_model_client() -> AnthropicModelClient:
    return AnthropicModelClient(
        model=ANTHROPIC_MODEL,
        thinking_enabled=EXTENDED_THINKING_ENABLED,
        thinking_budget_tokens=EXTENDED_THINKING_BUDGET_TOKENS,
    )


async def _load_tool_catalog() -> None:
    client = StdioMCPClient(MCP_SERVER_SCRIPT)
    try:
        await client.connect()
        tools = await client.list_tools()
        _TOOL_CATALOG.extend(ToolCatalogEntry(name=t.name, description=t.description) for t in tools)
    except MCPUnreachableError:
        # Info panel still renders (with an empty tool list) rather than
        # failing app startup entirely — the per-task reachability check
        # (specs/agent-spec.md §9 #1) is what actually gates task execution.
        pass
    finally:
        await client.close()


async def _run_and_store(task_id: str, task_input: str) -> None:
    model_client = _make_model_client()
    mcp_client = StdioMCPClient(MCP_SERVER_SCRIPT)
    trace = await run_task(
        task_id=task_id,
        task_input=task_input,
        model_client=model_client,
        mcp_client=mcp_client,
        system_prompt=load_system_prompt(),
    )
    _TASKS[task_id] = trace


@app.post("/api/tasks", response_model=TaskSubmitResponse)
async def submit_task(body: TaskSubmitRequest) -> TaskSubmitResponse:
    if not body.task.strip():
        raise HTTPException(status_code=422, detail="task must not be empty or whitespace-only")

    task_id = str(uuid.uuid4())
    _TASKS[task_id] = TaskTrace(
        task_id=task_id,
        task_input=body.task,
        status=TaskStatus.IN_PROGRESS,
        limit_hit=LimitHit.NONE,
        tool_calls=[],
        final_answer=None,
        failure_reason=None,
        model=ANTHROPIC_MODEL,
        total_duration_ms=0,
        grounding_check=None,
    )
    asyncio.create_task(_run_and_store(task_id, body.task))
    return TaskSubmitResponse(task_id=task_id, status=TaskStatus.IN_PROGRESS)


@app.get("/api/tasks/{task_id}", response_model=TaskTrace)
async def get_task(task_id: str) -> TaskTrace:
    trace = _TASKS.get(task_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="unknown task_id")
    return trace


@app.get("/api/info", response_model=AgentInfo)
async def get_info() -> AgentInfo:
    return AgentInfo(
        model=ANTHROPIC_MODEL,
        tools=_TOOL_CATALOG,
        iteration_cap=ITERATION_CAP,
        per_call_timeout_s=PER_CALL_TIMEOUT_S,
        total_timeout_s=TOTAL_TASK_TIMEOUT_S,
    )
