"""Loads the product agent's system prompt verbatim.

specs/agent-spec.md §16: "a raw text file ... so there is exactly one copy
Phase 2 loads directly (open('prompts/system_prompt.txt').read())". Loaded
once at import time and cached — the file is static build content, not
per-request data.
"""

from __future__ import annotations

from config import REPO_ROOT

_PROMPT_PATH = REPO_ROOT / "prompts" / "system_prompt.txt"

_cached: str | None = None


def load_system_prompt() -> str:
    global _cached
    if _cached is None:
        _cached = _PROMPT_PATH.read_text(encoding="utf-8")
    return _cached
