# Self-Assessment Checklist

Every requirement and grading criterion extracted from `2026 AI Engineering Assessment.pdf`,
tracked here so we can self-assess before submission instead of discovering a gap too late. Update
the Status column as we build; don't mark Done until it's actually true. `Evidence` should point at
a file, commit, or section — not just assert compliance.

Status legend: `TODO` / `DOING` / `DONE` / `CUT` (deliberately descoped — must have a reason).

## Hard constraints (binary — either satisfied or the submission fails the brief)

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| C1 | Tools consumed **over MCP** — no tool wired directly into the backend outside the protocol | DONE | `backend/mcp_client.py` (`StdioMCPClient`) connects to `mcp-server/server.py` only over the real MCP stdio protocol — no direct Python import of the server's tool functions anywhere in `backend/`. Verified: `backend/tests/test_real_mcp_integration.py` (3 tests, real subprocess + real protocol). |
| C2 | Tool selection is the **model's decision** inside a bounded agent loop — no hardcoded call sequence | DONE | `backend/agent_loop.py` never chooses a tool — it only executes whatever `response.tool_uses` the model returned. Bounded by `ITERATION_CAP`/timeouts, not by a fixed call sequence. |

## Backend

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| B1 | Python backend, exposes an API consumed by the frontend | DONE | `backend/main.py` (FastAPI) — `CLAUDE.md` §"Backend API contract" |
| B2 | Agent loop connects to the MCP server, presents tools to the model, executes model-chosen calls, feeds results back | DONE | `backend/agent_loop.py` |
| B3 | Supports multiple tool calls per task | DONE | `backend/tests/test_agent_loop_happy_path.py` (multi-target dairy suppliers scenario) |
| B4 | Loop is bounded: iteration cap | DONE | `ITERATION_CAP = 8`, `backend/tests/test_loop_bounds.py` |
| B5 | Loop is bounded: timeouts | DONE | 10s/call, 60s total, `backend/tests/test_loop_bounds.py` |
| B6 | Unreachable MCP server → meaningful state, not a hang/crash | DONE | `backend/tests/test_agent_loop_failures.py::test_mcp_server_unreachable_at_task_start` |
| B7 | Tool call errors mid-task → meaningful state, not a hang/crash | DONE | `backend/tests/test_agent_loop_failures.py::test_tool_call_error_mid_task_sets_completed_partial` |
| B8 | Model failure → meaningful state, not a hang/crash | DONE | `backend/tests/test_agent_loop_failures.py::test_model_api_failure_mid_task`; unexpected internal faults get their own `INTERNAL_ERROR` bucket (`ai/build-loop-fix-log.md` gap #3) |
| B9 | Secrets taken from environment only; nothing sensitive committed | DONE | `backend/config.py` reads `ANTHROPIC_API_KEY` at call time only, never stored/logged; `.gitignore` excludes `.env*` |

## Frontend

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| F1 | React (TypeScript encouraged) | TODO | |
| F2 | User can submit a task and see progress + result, with 4 distinct overall states (in progress/completed/completed-partial/failed) | TODO | `CLAUDE.md` §"Frontend transparency requirements" |
| F3 | Per tool call: shows tool name, input, result summary, **and explicit success/error status** (not folded together) | TODO | `CLAUDE.md` §"Frontend transparency requirements"; trace schema in `specs/mcp-integration-spec.md` §10 |
| F4 | A user can look at a completed task and understand what the agent did and why the answer is what it is (this is the transparency bar, not just "logs exist") | TODO | |
| F5 | Sensible, visually distinct states shown for each of the 3 failure modes (MCP unreachable / tool error / model failure) — user can tell *which* failure happened | TODO | `specs/agent-spec.md` §9 "Escalation / Failure Behaviour" |
| F6 | Explicit limit-hit indicator (iteration cap or timeout) shown as its own labelled state, never silently blended into a normal-looking answer | TODO | `limit_hit` field, `specs/mcp-integration-spec.md` §10 |
| F7 | Per-call `reasoning` note shown (why the agent called that tool) + static "how this agent works" info panel + final-answer basis line (call counts/model/time) + raw-trace-JSON view | TODO | `CLAUDE.md` §"Frontend transparency requirements" #3/#5/#7/#8; `design/ui-mockup/` |
| F8 | Raw extended-thinking shown per tool-call step, collapsed by default, with a clear non-authoritative caption | TODO | `specs/agent-spec.md` §10 "On Chain-of-Thought"; `thinking` field, `specs/mcp-integration-spec.md` §10 |
| F9 | (Added P27) Grounding-check warning shown when the final answer references an entity never returned by any tool — distinct from, and shown regardless of, task completion status | TODO | `CLAUDE.md` §"Frontend transparency requirements" #9; AC15; `specs/agent-spec.md` §17 |

## Model access

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| M1 | Own API key, mainstream provider (or clearly signposted mock adapter behind the same interface if no key) | DONE | Anthropic API key confirmed by user, `ai/DECISIONS.md` §4 |
| M2 | If mock adapter used: MCP service chosen must not itself require paid access | N/A | Not using a mock adapter |

## Testing

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| T1 | Automated tests "where they earn their place" | DOING | 19 backend tests (`backend/tests/`) against `FakeModelClient`/`FakeMCPClient`, no network/spend needed, plus 3 real-MCP-protocol integration tests. Still to add (Phase 4, `ai/ROADMAP.md`): `mcp-server/tests/` for E1–E6, and one true HTTP-level end-to-end test (real `run_task()` over the API, not stubbed). Deliberately not adding: an automated test against the real Anthropic API (cost/flakiness) — real-model verification stays manual, recorded as a deliberate cut. |
| T2 | Happy path covered end-to-end | DONE | `backend/tests/test_agent_loop_happy_path.py` |
| T3 | 2–3 failure scenarios covered (MCP unreachable, tool error mid-task, model/API failure) | DONE | `backend/tests/test_agent_loop_failures.py` (all 3) |
| T4 | 5–6 validation edge cases covered (empty results, zero-cert supplier, invalid enum, embedded-instruction content, allergen boundaries, expiry boundary) | TODO | `CLAUDE.md` §"Testing scenarios & required mock data" — these are MCP-server-level (`mcp-server/`) tests, not yet written as a formal suite (verified manually during Phase 1, `ai/DECISIONS.md` §24) |
| T5 | Loop-bound enforcement specifically tested (iteration cap, timeouts) | DONE | `backend/tests/test_loop_bounds.py` |
| T6 | (Added P29) Grounding mechanical backstop tested | DONE | `backend/tests/test_grounding.py` (4 tests, incl. end-to-end "model invents an ID" case) |
| T7 | (Added P29) Dedup safety net (R2/R5) tested | DONE | `backend/tests/test_dedup.py` |

## Deliverables

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| D1 | Git repo with real history — commits that tell the story, not one final commit | DONE | GitHub public repo `foods-connected-compliance-assistant`, 8+ commits with descriptive multi-line messages, one per phase/milestone (Phases 0–2, closed-build-loop pass, checkpoints) |
| D2 | `ai/` directory with agent instruction files (CLAUDE.md etc.) | DONE | `CLAUDE.md` (root, referenced from `ai/`), current through P31 |
| D3 | `ai/` directory with significant prompts | DOING | `ai/prompts.md`, P1–P31 logged verbatim; append-only, kept current as the build continues |
| D4 | `ai/` directory with transcripts or session summaries | DONE | `ai/prompts.md` (transcript — the brief says "transcripts *or* session summaries"; `ai/session-summary.md` is a bonus presentation-prep narrative, not needed for compliance) |
| D5 | `ai/` directory with a note on which tools/models were used | DONE | `ai/tools-and-models.md` |
| D6 | README: how to run, incl. env vars and mock-adapter toggle if any | DONE | `README.md` §"How to run" (mcp-server + backend, `ANTHROPIC_API_KEY` env var); frontend row still `[TODO — Phase 3]` inside that same section, to be filled when Phase 3 lands |
| D7 | README: chosen use case and MCP service | DONE | `README.md` §"Use case & MCP service"; full reasoning `ai/DECISIONS.md` §5/§8 |
| D8 | README: key decisions | DONE | `README.md` §"Key decisions" (highlights + pointer to full `ai/DECISIONS.md` log) |
| D9 | README: known limitations | DOING | `README.md` §"Known limitations" has the multi-turn-follow-up cut written up; placeholder line still needs real Phase 3–5 gaps folded in at Phase 6 wrap-up |
| D10 | README: what's next with more time | DOING | `README.md` §"What's next, with more time" has item 1 written; placeholder for further items at Phase 6 wrap-up |
| D11 | Time-boxed to ~4h; if scope is cut, record what and why | DOING | `ai/ROADMAP.md` frames the budget and now names one deliberate cut early (no automated real-API test, Phase 4); gap log finalised at Phase 6 |

## What gets assessed (qualitative — self-check before submitting)

| # | Dimension | Self-check question | Status | Evidence |
|---|-----------|---------------------|--------|----------|
| A1 | Agent design | Would a reviewer find the system prompt, tool exposure, loop bounds, and failure handling well-reasoned, not just present? | TODO | `specs/agent-spec.md` (tool-selection rules, delegation boundaries, validation, assumptions) |
| A2 | Untrusted content handling | Does the design explicitly treat MCP tool results as untrusted input (not blindly followed as instructions)? See `CLAUDE.md` hard constraint on this. | TODO | `specs/agent-spec.md` §7 (untrusted content) + §15/§17 (grounding rule + mechanical anti-hallucination backstop) |
| A3 | Codebase quality | Would I be comfortable with this being read as production code carrying my name? | TODO | |
| A4 | Frontend transparency | Does the UI faithfully show what the agent actually did, or does it paper over/simplify in a way that could mislead? | TODO | |
| A5 | AI-tool direction & verification | Is there enough evidence (commits, `ai/` artefacts, prompts) to show *how* the build was directed and checked, not just that AI was used? | DOING | |
| A6 | Judgement over feature tour | Can I articulate, in the presentation, where I intervened and what the AI got wrong? | TODO | |

## Presentation coverage (15 min + Q&A)

| # | Must cover | Status |
|---|------------|--------|
| P1 | Chosen use case and MCP service, and why | TODO |
| P2 | Agent design: system prompt, tool presentation, loop bounds, failure handling | TODO |
| P3 | How AI tools were directed during the build: instructions, prompts, iterations | TODO |
| P4 | What the AI got wrong — in the product or in the build — how it was caught, what was done about it | TODO |
