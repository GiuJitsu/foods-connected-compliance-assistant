# Build Loop Fix Log — Phase 2 (Backend Agent Loop)

Closed-build-loop pass, run per the user's explicit request (P29) using the training program's own
three-part build prompt: *"Begin building the agent described in this document. First, tell me
what you can build confidently without asking questions. Second, tell me what you need to clarify
before building the rest. Third, build the parts you are confident about."*

**Run against a fresh subagent, not me** — I wrote every spec file; building against my own specs
myself would test my memory of intent, not whether the documents are actually self-sufficient. A
subagent with no conversation history was given only: `CLAUDE.md`, `specs/agent-spec.md`,
`specs/mcp-integration-spec.md`, `prompts/system_prompt.txt`, and the already-built/verified
`mcp-server/`. It was explicitly told not to read `ai/DECISIONS.md`, `ai/prompts.md`, or
`AI FDE Training/` — anything it needed that wasn't in those five sources was, by design, a real
spec gap to report, not something to go find elsewhere.

(Process note: the first dispatch of this subagent appeared to be interrupted by the user before it
started, but had in fact already begun running and completed in the background — `backend/` existed
before the second dispatch, which sensibly reviewed/verified rather than rewrote it. All findings
below are independently re-verified by me, not taken on the subagent's word: I ran the full test
suite myself — 19/19 pass — and read `agent_loop.py`, `grounding.py`, `main.py`, `schemas.py`,
`config.py` directly.)

## What it built (verified faithful)

`backend/`: `agent_loop.py` (the bounded loop), `grounding.py` (the mechanical backstop, §17),
`main.py` (FastAPI endpoints), `model_client.py` / `mcp_client.py` (swappable real + fake
implementations), `config.py`, `system_prompt.py`, `schemas.py` (trace schema), plus a 19-test
suite including 3 tests that exercise the real MCP server over actual stdio protocol. Cross-checked
against `specs/agent-spec.md` and `specs/mcp-integration-spec.md` line by line: loop bounds,
trace-schema field names/enums, `reasoning`-required enforcement, the R2/R5 dedup safety net, and
the grounding backstop's exact regex/diff mechanism all match. No drift found beyond the 5 gaps
below.

## What it could not build

Nothing genuinely blocked. `AnthropicModelClient` is fully implemented but intentionally never
exercised against the live API (no key provided, per instruction — spending real credits isn't the
builder's call). The React frontend is Phase 3, correctly out of scope.

## Gap log

| # | Gap | Category | Fix |
|---|---|---|---|
| 1 | No file specifies the HTTP endpoint contract (routes, methods, polling vs. streaming) — nothing in any of the 5 source files addresses this at all | **Design Gap** — a whole category (API contract) was never specified, not an ambiguous phrasing | **Ratify the builder's choice.** `POST /api/tasks` → immediate `{task_id, status: IN_PROGRESS}`; `GET /api/tasks/{id}` → poll for the current `TaskTrace`; `GET /api/info` → static info panel data. Sensible, RESTful, satisfies AC2/AC12. Locked into `CLAUDE.md` as the official contract so Phase 3 doesn't have to reverse-engineer it from `main.py`. |
| 2 | Exact model ID never locked — `specs/mcp-integration-spec.md` §10 gave `'claude-haiku-4-5'` only as an illustrative `"e.g."`, not a commitment. Builder correctly refused to guess a snapshot date and made it env-configurable with that placeholder as default | **Spec Ambiguity** — my own doc used example syntax ambiguously (looked normative, was meant as illustrative) | **Fixed with real information the builder didn't have access to**: the actual current model id is `claude-haiku-4-5-20251001`. Updated `backend/config.py`'s default and locked the exact string into `CLAUDE.md`/`specs/agent-spec.md` so it's no longer an "e.g." anywhere. |
| 3 | `FailureReason` enum only has `MCP_UNREACHABLE` / `MODEL_API_FAILURE` — an unexpected internal exception (a genuine backend bug) has no bucket, currently mapped to `MODEL_API_FAILURE` as the nearest existing value, which is misleading (implies the model/API failed when the bug is ours) | **Design Gap** — the enum's two members were clear; a third real category (internal fault) was never considered | **Add `INTERNAL_ERROR`** to the enum in `specs/mcp-integration-spec.md` §10 and `backend/schemas.py`; update `agent_loop.py`'s catch-all exception handler to use it instead of borrowing `MODEL_API_FAILURE`. |
| 4 | `status = COMPLETED_PARTIAL` currently fires whenever *any* tool call failed, even if the model successfully worked around it and fully answered — `specs/agent-spec.md` §9 #2 said "otherwise" (implying partial only when *no* alternative existed), a stricter reading than the code implements | **Spec Ambiguity** — "otherwise" was genuinely underspecified about what counts as successfully recovering | **Ratify the stricter behaviour as the locked interpretation**, don't change the code: any failed call sets `COMPLETED_PARTIAL` regardless of apparent recovery. Chosen because judging "did the model actually fully compensate" is itself a semantic call Python can't make reliably — erring toward flagging for visibility is consistent with this project's transparency-first stance throughout. `specs/agent-spec.md` §9 updated to state this explicitly, removing the "otherwise" ambiguity for future readers. |
| 5 | When one model turn emits multiple `tool_use` blocks sharing a single `thinking` block, the same `thinking` text is copied into every resulting trace entry — not addressed in the schema | **Design Gap** (borderline Acceptable Variation) — reasonable, defensible default; the schema just never said what "this step's thinking" means when one thinking block spans several tool calls | **Ratify as correct.** Documented explicitly in `specs/mcp-integration-spec.md` §10: when a turn has multiple tool calls, they share the turn's one `thinking` block, copied into each entry — not a per-call 1:1 mapping. No code change. |

## Status

All 5 gaps resolved this pass — 2 ratified as-is with the spec updated to match, 2 require a small
code change (model id default, new enum value + one call site), 1 (API contract) newly locked in
`CLAUDE.md`. Applying now; see `ai/DECISIONS.md` §30 for the full reasoning and `git log` for the
commit implementing these.
