# Self-Assessment Checklist

Every requirement and grading criterion extracted from `2026 AI Engineering Assessment.pdf`,
tracked here so we can self-assess before submission instead of discovering a gap too late. Update
the Status column as we build; don't mark Done until it's actually true. `Evidence` should point at
a file, commit, or section — not just assert compliance.

Status legend: `TODO` / `DOING` / `DONE` / `CUT` (deliberately descoped — must have a reason).

## Hard constraints (binary — either satisfied or the submission fails the brief)

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| C1 | Tools consumed **over MCP** — no tool wired directly into the backend outside the protocol | DOING | `mcp-server/server.py` (FastMCP, stdio transport, 5 tools) — tool logic verified directly AND the real MCP stdio protocol verified separately (handshake, list_tools, call_tool over actual JSON-RPC), `ai/DECISIONS.md` §24/P25. Remaining: Phase 2's backend needs to be the one actually doing this connection in the real app, not a scratch script. |
| C2 | Tool selection is the **model's decision** inside a bounded agent loop — no hardcoded call sequence | TODO | |

## Backend

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| B1 | Python backend, exposes an API consumed by the frontend | TODO | |
| B2 | Agent loop connects to the MCP server, presents tools to the model, executes model-chosen calls, feeds results back | TODO | |
| B3 | Supports multiple tool calls per task | TODO | |
| B4 | Loop is bounded: iteration cap | TODO | |
| B5 | Loop is bounded: timeouts | TODO | |
| B6 | Unreachable MCP server → meaningful state, not a hang/crash | TODO | |
| B7 | Tool call errors mid-task → meaningful state, not a hang/crash | TODO | |
| B8 | Model failure → meaningful state, not a hang/crash | TODO | |
| B9 | Secrets taken from environment only; nothing sensitive committed | TODO | |

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
| T1 | Automated tests "where they earn their place" | TODO | |
| T2 | Happy path covered end-to-end | TODO | |
| T3 | 2–3 failure scenarios covered (MCP unreachable, tool error mid-task, model/API failure) | TODO | |
| T4 | 5–6 validation edge cases covered (empty results, zero-cert supplier, invalid enum, embedded-instruction content, allergen boundaries, expiry boundary) | TODO | `CLAUDE.md` §"Testing scenarios & required mock data" |
| T5 | Loop-bound enforcement specifically tested (iteration cap, timeouts) | TODO | |

## Deliverables

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| D1 | Git repo with real history — commits that tell the story, not one final commit | TODO | Not yet git-initialised; will confirm with user before `git init` |
| D2 | `ai/` directory with agent instruction files (CLAUDE.md etc.) | DOING | `CLAUDE.md` (root, referenced from `ai/`) |
| D3 | `ai/` directory with significant prompts | DOING | `ai/prompts.md` |
| D4 | `ai/` directory with transcripts or session summaries | DONE | `ai/prompts.md` (transcript — the brief says "transcripts *or* session summaries"; `ai/session-summary.md` is a bonus presentation-prep narrative, not needed for compliance) |
| D5 | `ai/` directory with a note on which tools/models were used | DONE | `ai/tools-and-models.md` |
| D6 | README: how to run, incl. env vars and mock-adapter toggle if any | TODO | |
| D7 | README: chosen use case and MCP service | DONE | `README.md` §"Use case & MCP service"; full reasoning `ai/DECISIONS.md` §5/§8 |
| D8 | README: key decisions | TODO | Content ready in `ai/DECISIONS.md`, needs summarising into README |
| D9 | README: known limitations | TODO | |
| D10 | README: what's next with more time | TODO | |
| D11 | Time-boxed to ~4h; if scope is cut, record what and why | DOING | `ai/ROADMAP.md` frames the budget; gap log there will capture cuts |

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
