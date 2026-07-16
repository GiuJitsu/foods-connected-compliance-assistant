"""Environment-sourced configuration.

CLAUDE.md hard constraint #3: secrets come from the environment only, never
committed. Nothing here has a hardcoded secret; ANTHROPIC_API_KEY is read at
call time by model_client.AnthropicModelClient, not stored on import (so the
module can be imported — e.g. by tests using FakeModelClient — with no key
present at all).

Model id: locked (ai/build-loop-fix-log.md gap #2) to claude-haiku-4-5-20251001,
the real current Anthropic model id — the closed-build-loop pass that built
this file correctly refused to guess a snapshot date it had no way to know;
resolved here with information that fresh build didn't have access to. Still
env-overridable, not hardcoded as a secret or an assumption nothing can change.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# --- Model ---
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
# Extended thinking token budget — specs/agent-spec.md §10 says this is a value
# to calibrate empirically against real latency once Phase 2 exists ("watch
# actual per-call and total-task latency ... revisit if uncomfortable"), not a
# value the spec locks in. 1024 is a conservative starting point for a small
# tool-selection task, kept low to leave latency headroom under the 10s
# per-call bound. Override with EXTENDED_THINKING_BUDGET_TOKENS.
EXTENDED_THINKING_BUDGET_TOKENS = int(os.environ.get("EXTENDED_THINKING_BUDGET_TOKENS", "1024"))
EXTENDED_THINKING_ENABLED = os.environ.get("EXTENDED_THINKING_ENABLED", "true").lower() != "false"

# --- MCP server subprocess ---
MCP_SERVER_SCRIPT = str(REPO_ROOT / "mcp-server" / "server.py")
# Python executable used to spawn the MCP server subprocess. Defaults to the
# same interpreter running the backend (sys.executable is resolved by the
# caller, not here, to keep this module import-safe without sys side effects).
MCP_SERVER_PYTHON = os.environ.get("MCP_SERVER_PYTHON")  # None -> caller uses sys.executable

# --- Loop bounds (specs/agent-spec.md §3, CLAUDE.md "Quick facts") ---
ITERATION_CAP = 8
PER_CALL_TIMEOUT_S = 10
TOTAL_TASK_TIMEOUT_S = 60

# --- API ---
CORS_ALLOW_ORIGINS = os.environ.get("CORS_ALLOW_ORIGINS", "http://localhost:5173").split(",")
