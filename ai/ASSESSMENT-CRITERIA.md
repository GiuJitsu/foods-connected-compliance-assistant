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
| F1 | React (TypeScript encouraged) | DONE | `frontend/` — React 19 + TypeScript + Vite |
| F2 | User can submit a task and see progress + result, with 4 distinct overall states (in progress/completed/completed-partial/failed) | DONE | `StatusBanner.tsx` — all 4 verified: IN_PROGRESS/COMPLETED against the real backend (`e2e.spec.ts`), COMPLETED_PARTIAL (both `limit_hit` and plain-tool-failure cases) and FAILED (all 3 `failure_reason` values) against a schema-accurate mocked backend (`e2e-mocked-states.spec.ts`, Phase 5) |
| F3 | Per tool call: shows tool name, input, result summary, **and explicit success/error status** (not folded together) | DONE | `frontend/src/components/TraceList.tsx`; verified live — real trace rendered correctly in a real Playwright run, screenshot reviewed |
| F4 | A user can look at a completed task and understand what the agent did and why the answer is what it is (this is the transparency bar, not just "logs exist") | DONE | Confirmed by direct visual review of a real completed task's screenshot — reasoning, thinking, tool sequence, and answer all legible together |
| F5 | Sensible, visually distinct states shown for each of the 3 failure modes (MCP unreachable / tool error / model failure) — user can tell *which* failure happened | DONE | `FailureCard.tsx` — all 3 distinct copy blocks verified live via 3 mocked-backend Playwright tests (`e2e-mocked-states.spec.ts`), matching the same 3 scenarios `backend/tests/test_agent_loop_failures.py` proves the backend actually produces |
| F6 | Explicit limit-hit indicator (iteration cap or timeout) shown as its own labelled state, never silently blended into a normal-looking answer | DONE | `StatusBanner.tsx`/`AnswerCard.tsx` — both `ITERATION_CAP` and `TIMEOUT` verified live (`e2e-mocked-states.spec.ts`), matching `backend/tests/test_loop_bounds.py` |
| F7 | Per-call `reasoning` note shown (why the agent called that tool) + static "how this agent works" info panel + final-answer basis line (call counts/model/time) + raw-trace-JSON view | DONE | All four verified live in a real Playwright run against the real backend: `frontend/src/components/{TraceList,Sidebar,AnswerCard}.tsx` |
| F8 | Raw extended-thinking shown per tool-call step, collapsed by default, with a clear non-authoritative caption | DONE | `TraceList.tsx`; verified live — real extended-thinking content rendered under a collapsed disclosure in the real Playwright screenshot |
| F9 | (Added P27) Grounding-check warning shown when the final answer references an entity never returned by any tool — distinct from, and shown regardless of, task completion status | DONE | `AnswerCard.tsx` — PASSED verified against a real answer (`e2e.spec.ts`), FLAGGED verified against a mocked-but-schema-accurate payload (`e2e-mocked-states.spec.ts`, Phase 5 — a real hallucination isn't reliably reproducible on demand, but the render logic itself is now proven, and `backend/tests/test_grounding.py` separately proves the backend computes `FLAGGED` correctly when a model does invent an ID) |

## Model access

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| M1 | Own API key, mainstream provider (or clearly signposted mock adapter behind the same interface if no key) | DONE | Anthropic API key confirmed by user, `ai/DECISIONS.md` §4; actually exercised end-to-end against the real API in `backend/tests/test_real_llm_integration.py`, 3/3 passing — `ai/test-log.md` |
| M2 | If mock adapter used: MCP service chosen must not itself require paid access | N/A | Not using a mock adapter |

## Testing

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| T1 | Automated tests "where they earn their place" | DONE | 33/33 tests passing across `mcp-server/tests/` (10) and `backend/tests/` (23) — fake-model/fake-MCP, fake-model/real-MCP, real-HTTP-end-to-end, and real-model/real-MCP layers all covered, no gaps left. Full breakdown: `ai/test-log.md`. |
| T2 | Happy path covered end-to-end | DONE | `backend/tests/test_agent_loop_happy_path.py`; also exercised for real in `backend/tests/test_real_llm_integration.py` |
| T3 | 2–3 failure scenarios covered (MCP unreachable, tool error mid-task, model/API failure) | DONE | `backend/tests/test_agent_loop_failures.py` (all 3) |
| T4 | 5–6 validation edge cases covered (empty results, zero-cert supplier, invalid enum, embedded-instruction content, allergen boundaries, expiry boundary) | DONE | `mcp-server/tests/test_edge_cases.py` (10 tests, one per E1–E6 plus NOT_FOUND contracts), `ai/test-log.md` |
| T5 | Loop-bound enforcement specifically tested (iteration cap, timeouts) | DONE | `backend/tests/test_loop_bounds.py` |
| T6 | (Added P29) Grounding mechanical backstop tested | DONE | `backend/tests/test_grounding.py` (4 tests, incl. end-to-end "model invents an ID" case) |
| T7 | (Added P29) Dedup safety net (R2/R5) tested | DONE | `backend/tests/test_dedup.py` |

## Deliverables

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| D1 | Git repo with real history — commits that tell the story, not one final commit | DONE | GitHub public repo `foods-connected-compliance-assistant`, 8+ commits with descriptive multi-line messages, one per phase/milestone (Phases 0–2, closed-build-loop pass, checkpoints) |
| D2 | `ai/` directory with agent instruction files (CLAUDE.md etc.) | DONE | `CLAUDE.md` (root, referenced from `ai/`), current through P31 |
| D3 | `ai/` directory with significant prompts | DONE | `ai/prompts.md`, P1–P40 logged verbatim, append-only; kept current as the build continues (still growing, but the requirement is satisfied continuously, not blocked on anything) |
| D4 | `ai/` directory with transcripts or session summaries | DONE | `ai/prompts.md` (transcript — the brief says "transcripts *or* session summaries"; `ai/session-summary.md` is a bonus presentation-prep narrative, not needed for compliance) |
| D5 | `ai/` directory with a note on which tools/models were used | DONE | `ai/tools-and-models.md` |
| D6 | README: how to run, incl. env vars and mock-adapter toggle if any | DONE | `README.md` §"How to run" — mcp-server, backend (`ANTHROPIC_API_KEY`), frontend (`npm run dev`, `VITE_API_BASE_URL`), and the Playwright test suite, all with real runnable commands |
| D7 | README: chosen use case and MCP service | DONE | `README.md` §"Use case & MCP service"; full reasoning `ai/DECISIONS.md` §5/§8 |
| D8 | README: key decisions | DONE | `README.md` §"Key decisions" (highlights + pointer to full `ai/DECISIONS.md` log) |
| D9 | README: known limitations | DOING | `README.md` §"Known limitations" has the multi-turn-follow-up cut written up; placeholder line still needs real Phase 3–5 gaps folded in at Phase 6 wrap-up |
| D10 | README: what's next with more time | DOING | `README.md` §"What's next, with more time" has item 1 written; placeholder for further items at Phase 6 wrap-up |
| D11 | Time-boxed to ~4h; if scope is cut, record what and why | DOING | `ai/ROADMAP.md` frames the budget and now names one deliberate cut early (no automated real-API test, Phase 4); gap log finalised at Phase 6 |

## What gets assessed (qualitative — self-check before submitting)

| # | Dimension | Self-check question | Status | Evidence |
|---|-----------|---------------------|--------|----------|
| A1 | Agent design | Would a reviewer find the system prompt, tool exposure, loop bounds, and failure handling well-reasoned, not just present? | DONE | `specs/agent-spec.md` (§1–§17: identity, tool-selection rules R1–R6, delegation boundaries, validation, assumptions register); `prompts/system_prompt.txt` the literal runtime text; empirically confirmed working against the real model (`ai/test-log.md`, `ai/DECISIONS.md` §32) |
| A2 | Untrusted content handling | Does the design explicitly treat MCP tool results as untrusted input (not blindly followed as instructions)? See `CLAUDE.md` hard constraint on this. | DONE | `specs/agent-spec.md` §7 (untrusted content) + §15/§17 (grounding rule + mechanical anti-hallucination backstop); E4 fixture (`INC-003`'s embedded-instruction text) confirmed round-tripping unmodified in `mcp-server/tests/test_edge_cases.py`; grounding backstop tested end-to-end in `backend/tests/test_grounding.py` and live in the frontend (`frontend/tests/e2e-mocked-states.spec.ts`) |
| A3 | Codebase quality | Would I be comfortable with this being read as production code carrying my name? | TODO | This is the user's own self-assessment, not something Claude Code marks on their behalf — worth a deliberate read-through at Phase 6 wrap-up |
| A4 | Frontend transparency | Does the UI faithfully show what the agent actually did, or does it paper over/simplify in a way that could mislead? | DONE | `frontend/` — every status/error/limit/grounding state verified live via Playwright, real backend for the happy/partial path and a schema-accurate mocked backend for the states a real run can't reliably force on demand (`ai/DECISIONS.md` §34/§35) |
| A5 | AI-tool direction & verification | Is there enough evidence (commits, `ai/` artefacts, prompts) to show *how* the build was directed and checked, not just that AI was used? | DONE | `ai/prompts.md` (P1–P40, verbatim), `ai/DECISIONS.md` (35 numbered sections with reasoning), `ai/build-loop-fix-log.md`, `ai/test-log.md`, git history (descriptive multi-line commits at every phase) — all cross-referenced, not just present |
| A6 | Judgement over feature tour | Can I articulate, in the presentation, where I intervened and what the AI got wrong? | TODO | Concrete material ready to draw on: the React StrictMode polling bug found via Playwright (`ai/DECISIONS.md` §34), the 5 closed-build-loop gaps from Phase 2 (`ai/build-loop-fix-log.md`), the E4 spec-gap correction (`ai/DECISIONS.md` §23) — this row is about live presentation capability, not something pre-completable |

## Presentation coverage (15 min + Q&A)

| # | Must cover | Status |
|---|------------|--------|
| P1 | Chosen use case and MCP service, and why | TODO |
| P2 | Agent design: system prompt, tool presentation, loop bounds, failure handling | TODO |
| P3 | How AI tools were directed during the build: instructions, prompts, iterations | TODO |
| P4 | What the AI got wrong — in the product or in the build — how it was caught, what was done about it | TODO |
