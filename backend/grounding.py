"""Grounding mechanical backstop (specs/agent-spec.md §17, added P27).

After the loop produces a final answer, extract every ID-shaped token from
the answer text via regex, collect every entity ID that appeared in *any*
tool result during the task's trace, and flag any answer-side ID not in that
set. This is a deterministic, Python-side safety net alongside (not instead
of) the system prompt's grounding instruction (specs/agent-spec.md §15) —
belt-and-braces, same pattern as the `reasoning` structural enforcement (§6).

Explicit, named limits (stated in the spec, repeated here so the code and its
own comments don't drift apart): this catches invented *entity references*
only — a hallucinated fact about a real, correctly-cited entity, or a
name-only hallucination with no ID attached, is invisible to this check. Not
a full semantic fact-check; out of scope for this build (specs/agent-spec.md
§17).
"""

from __future__ import annotations

import re
from typing import Any

from schemas import GroundingCheck, GroundingStatus

# Exact patterns from specs/agent-spec.md §17, matching mockdata/'s actual ID
# conventions (SUP-001, SUP-TIMEOUT-01, CERT-001, SPEC-001, INC-001).
_ID_PATTERNS = [
    re.compile(r"\bSUP-[A-Z0-9-]+\b"),
    re.compile(r"\bCERT-\d+\b"),
    re.compile(r"\bSPEC-\d+\b"),
    re.compile(r"\bINC-\d+\b"),
]


def extract_id_tokens(text: str) -> set[str]:
    """Every ID-shaped token found in `text`, per the four patterns above."""
    found: set[str] = set()
    for pattern in _ID_PATTERNS:
        found.update(pattern.findall(text))
    return found


def collect_known_ids_from_tool_results(tool_results: list[dict[str, Any]]) -> set[str]:
    """Walk every tool result payload from this task's trace and collect
    every string value found under an `id` key or any `*_id` foreign-key key,
    at any nesting depth — "not just the ones directly requested — every `id`
    and foreign-key field in every response" (specs/agent-spec.md §17)."""
    known: set[str] = set()

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(value, str) and (key == "id" or key.endswith("_id")):
                    known.add(value)
                _walk(value)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    for result in tool_results:
        _walk(result)
    return known


def compute_grounding_check(final_answer: str, tool_results: list[dict[str, Any]]) -> GroundingCheck:
    referenced = extract_id_tokens(final_answer)
    known = collect_known_ids_from_tool_results(tool_results)
    unrecognized = sorted(referenced - known)
    status = GroundingStatus.FLAGGED if unrecognized else GroundingStatus.PASSED
    return GroundingCheck(status=status, unrecognized_references=unrecognized)
