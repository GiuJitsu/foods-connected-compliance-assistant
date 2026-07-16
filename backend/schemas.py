"""Trace/task Pydantic models for the Compliance Assistant backend.

Matches the schema defined in specs/mcp-integration-spec.md §10 exactly (field
names, enums, nesting). This is the object the API returns to the frontend and
that the frontend's "view raw trace JSON" affordance (CLAUDE.md §"Frontend
transparency requirements" #8) exposes verbatim.

Deliberately separate from mcp-server/schemas.py (entity/tool-input schemas for
the MCP server itself) — this file describes the *backend's own* task/trace
bookkeeping, not the MCP tool contracts. The backend talks to the MCP server
only over the MCP protocol (stdio), never by importing mcp-server's Python
modules directly (see mcp-integration-spec.md §2 "Transport").
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    COMPLETED_PARTIAL = "COMPLETED_PARTIAL"
    FAILED = "FAILED"


class LimitHit(str, Enum):
    NONE = "NONE"
    ITERATION_CAP = "ITERATION_CAP"
    TIMEOUT = "TIMEOUT"


class ToolErrorType(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    TIMEOUT = "TIMEOUT"
    SERVER_ERROR = "SERVER_ERROR"


class FailureReason(str, Enum):
    MCP_UNREACHABLE = "MCP_UNREACHABLE"
    MODEL_API_FAILURE = "MODEL_API_FAILURE"
    # Added ai/build-loop-fix-log.md gap #3: an unexpected internal exception
    # (a genuine backend bug) previously had no bucket and was misleadingly
    # mapped to MODEL_API_FAILURE. Distinct from it so a reviewer isn't misled
    # into thinking the model/API was at fault when the bug is ours.
    INTERNAL_ERROR = "INTERNAL_ERROR"


class GroundingStatus(str, Enum):
    PASSED = "PASSED"
    FLAGGED = "FLAGGED"


class ToolCallError(BaseModel):
    type: ToolErrorType
    message: str


class ToolCallTrace(BaseModel):
    """One entry per tool call, in order (mcp-integration-spec.md §10)."""

    timestamp: str  # ISO 8601
    tool_name: str
    input: dict
    reasoning: str
    thinking: Optional[str] = None
    result_summary: str
    success: bool
    error: Optional[ToolCallError] = None
    latency_ms: int


class GroundingCheck(BaseModel):
    status: GroundingStatus
    unrecognized_references: list[str] = Field(default_factory=list)


class TaskTrace(BaseModel):
    """Task-level summary wrapping the ordered tool-call trace (§10)."""

    task_id: str
    task_input: str
    status: TaskStatus
    limit_hit: LimitHit = LimitHit.NONE
    tool_calls: list[ToolCallTrace] = Field(default_factory=list)
    final_answer: Optional[str] = None
    failure_reason: Optional[FailureReason] = None
    model: str
    total_duration_ms: int = 0
    grounding_check: Optional[GroundingCheck] = None


class TaskSubmitRequest(BaseModel):
    task: str = Field(min_length=1)


class TaskSubmitResponse(BaseModel):
    task_id: str
    status: TaskStatus


class ToolCatalogEntry(BaseModel):
    name: str
    description: str


class AgentInfo(BaseModel):
    """Static "how this agent works" info panel data (CLAUDE.md §"Frontend
    transparency requirements" #7 / AC12)."""

    model: str
    tools: list[ToolCatalogEntry]
    iteration_cap: int
    per_call_timeout_s: int
    total_timeout_s: int
