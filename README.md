# Foods Connected — Compliance Assistant

> **Status: living document. Phase 0, 0.5, and 1 (spec, UI mockup, mock data + MCP server) are
> complete and verified — the MCP server actually runs and every tool has been tested directly.
> Phase 2 (backend agent loop) is next.** Sections below are written against the spec in
> `CLAUDE.md` and `specs/agent-spec.md`, and will be completed/corrected as each build phase lands
> — see `ai/ROADMAP.md` for the phase-by-phase plan and current position. Repo:
> https://github.com/GiuJitsu/foods-connected-compliance-assistant

A take-home technical assessment (AI Engineering role, Foods Connected): a web app where a user
submits a task in natural language, a Python backend runs a bounded AI agent loop over a
custom MCP server to complete it, and a React frontend shows exactly what the agent did and why.

## Purpose

This isn't a real product — it's a scoped demonstration of agent engineering: designing an agent
loop with real bounds and real failure handling, consuming tools strictly over MCP with the model
choosing which tools to call, and making that reasoning fully visible to the end user. The scenario
is a "Compliance Assistant" for a mock food-supply-chain dataset, deliberately shaped to mirror
Foods Connected's real Compliance & Food Safety / Quality Management / Product Lifecycle Management
product areas (see "Use case & MCP service" below) — but all data in this project is fabricated;
no real Foods Connected client, supplier, or product data is used anywhere.

## User handbook — how to use this app

1. **Submit a task.** Type a natural-language question about the mock supplier/compliance dataset
   (e.g. *"Which dairy suppliers have an expired certification?"*) and submit it. Each submission
   is a **single, independent task** — there is no follow-up or chat memory between tasks; a new
   question is a fresh, unrelated run (see "Known limitations").
2. **Watch the status.** A task is always in one of four states: **in progress**, **completed**,
   **completed with limit hit** (the agent ran out of tool-call budget or time and is giving you
   its best partial answer), or **failed** (something broke before an answer could be produced).
3. **Read the tool-activity trace.** Every tool call the agent made is listed, in order, showing:
   which tool, what input it sent, a one-line reason *why* it chose that tool, a summary of what
   came back, and whether that specific call succeeded or errored (and if it errored, which kind:
   invalid input, not found, timeout, or server error). This is what lets you see *why* the final
   answer is what it is, not just what the answer is.
4. **Check for a limit-hit flag.** If the agent stopped because it hit its call limit or ran out of
   time — rather than because it finished — this is shown explicitly, not silently folded into a
   normal-looking answer.
5. **Read the final answer's basis line.** Alongside the answer itself: how many tool calls
   succeeded/failed, which model produced it, and how long the task took — plus a "view raw trace
   JSON" link if you want the unprocessed data behind the summary.
6. **Check the always-visible info panel** at the top of the page for what model is answering,
   which tools it has access to, and its hard limits — visible before you even submit a task.
7. **If it failed**, the failure state tells you which of three things went wrong: the tool server
   was unreachable, a specific tool call errored mid-task, or the underlying model/API failed. You
   won't see a raw crash or a stack trace.

Visual reference for all of the above: [`design/ui-mockup/wireframe.svg`](design/ui-mockup/wireframe.svg)
(and its companion [`design/ui-mockup/NOTES.md`](design/ui-mockup/NOTES.md)).

## What you can ask — examples

Real questions the agent can answer against the actual mock dataset (see "Available data" below).
Each of these needs the agent to chain 2+ tool calls on its own — none of these are hardcoded paths:

- *"Which dairy suppliers have an expired certification?"* — searches suppliers by category, then
  checks each one's certifications.
- *"Is supplier SUP-013 currently compliant?"* — a direct lookup when an ID is already known.
- *"Are there any open recalls affecting Alpine Milk Co's products?"* — resolves the supplier, finds
  its specifications, then checks each for quality incidents.
- *"Does the Croissants 4pk specification contain any allergens I should avoid if I'm allergic to
  gluten and eggs?"* — a direct allergen-conflict check.
- *"Which suppliers in Italy have a valid BRCGS certification?"* — filtered search plus per-supplier
  verification.
- *"What quality incidents have there been for seafood suppliers this year?"* — a question with
  **no matching data by design** (worth trying deliberately — see below).

## Available data

The mock dataset (`mockdata/`, loaded by the MCP server at startup — see `specs/agent-spec.md` §15
for why the agent must never fabricate an answer when a query legitimately returns nothing):

| Entity | Count | Detail |
|---|---|---|
| Suppliers | 18 | Categories: Dairy, Produce, Meat, Bakery, Seafood. Countries: IT, FR, ES, NO, GB, DE, PL, LV. Risk ratings: Low/Medium/High. |
| Certifications | 20 | Standards: BRCGS, GLOBALG.A.P., ISO 22000, SALSA. Statuses: Valid, Expired, Suspended. One supplier (SUP-017) deliberately has zero certifications. |
| Product specifications | 25 | Allergen tags where relevant (milk, gluten, eggs, fish, shellfish, sesame, etc.); some have none. |
| Quality incidents | 10 | Types: Recall, Complaint, Non-conformance. Most specifications have none at all — a legitimate "no incidents found" answer, not a gap. |

Every record is fabricated for this demo — no real Foods Connected client, supplier, or product
data is used anywhere.

## Use case & MCP service

**Custom, self-built MCP server** over a mock food-supply-chain compliance dataset (suppliers,
certifications, product specifications, quality incidents) — five read-only tools, chosen over
GitHub's public MCP server. Why: thematic relevance to Foods Connected's actual product (grounded
in public research — see `ai/DECISIONS.md` §8), a fully deterministic offline demo (no live-API
flakiness during presentation), and full control to deliberately build in the failure-mode and
untrusted-content scenarios the assessment specifically grades. Full trade-off analysis:
`ai/DECISIONS.md` §5.

## MCP server & tools — built and verified (Phase 1)

The MCP server (`mcp-server/server.py`, Python `mcp` SDK, stdio transport) exposes 5 read-only
tools over the dataset above. Every tool requires a `reasoning` argument — schema-enforced, not
just requested — so the "why did the agent do that" trail can never be silently empty (full
rationale: `specs/agent-spec.md` §6).

| Tool | What it does |
|---|---|
| `search_suppliers` | Find suppliers by name, category, country, or risk rating |
| `get_supplier_profile` | Full profile for one supplier plus all its certifications |
| `search_specifications` | Find product specifications by name, supplier, or category |
| `search_quality_incidents` | Find recalls/complaints/non-conformances by specification, supplier, date, or type |
| `check_allergen_conflicts` | Check whether a specification's allergens overlap with a given avoid-list |

Full contracts (input/output schemas, error behaviour, retry policy): `specs/mcp-integration-spec.md`.
Built and verified at two levels (Phase 1, `ai/DECISIONS.md` §24): the tool logic directly (happy
path, every edge case E1–E6, the blank-`reasoning` rejection, the deliberate 12-second timeout
fixture), **and separately, the real MCP stdio protocol itself** (`ai/DECISIONS.md` §24 update,
P25) — a real client handshake, `list_tools`, and `call_tool` over actual JSON-RPC, confirming a
real agent can connect to this server and use it, not just that the underlying Python works.

## Architecture at a glance

```
mockdata/     — the mock dataset (JSON): suppliers, certifications, specifications, incidents
mcp-server/   — custom MCP server exposing 5 read-only tools over mockdata/
backend/      — Python (FastAPI) API + bounded agent loop (Anthropic API + MCP client)
frontend/     — React + TypeScript UI: task submission, status, tool-activity trace
specs/        — pre-build design specs (MCP tool contracts, full agent behaviour spec)
prompts/      — literal, directly-loadable prompt text (system_prompt.txt) used at runtime
design/       — UI wireframe + functional summary, designed before frontend code exists
ai/           — required submission artefacts: CLAUDE.md context, prompts, decisions, roadmap
```

Full technical spec (entities, tool contracts, agent design, loop bounds, failure handling): see
`CLAUDE.md` (project root) and `specs/mcp-integration-spec.md`.

## How to run

**MCP server (Phase 1 — runnable today):**
```
cd mcp-server
pip install -r requirements.txt
python server.py
```
Runs over stdio — it's meant to be spawned by the backend (Phase 2), not talked to directly in a
terminal. To sanity-check it standalone, `python -c "import server; print(server.search_suppliers(reasoning='test', category='DAIRY'))"`
from inside `mcp-server/` will run one tool call directly against the loaded mock data.

**Backend + frontend:** `[TODO — filled in once Phase 2–3 are built.]` Will include: required
environment variables (`ANTHROPIC_API_KEY` at minimum), startup commands for both, and — if a mock
model adapter is ever added — how to toggle it. No mock adapter is currently planned; a real
Anthropic API key is being used throughout (`ai/DECISIONS.md` §4).

## Key decisions

Full reasoning and chronological log: `ai/DECISIONS.md`. Highlights:
- Custom food-supply-chain MCP server over GitHub's public one — thematic fit + demo determinism.
- Single-shot task model, no multi-turn follow-up — matches the brief's framing, avoids unscoped
  chat-state complexity in a 4-hour build.
- Agent loop bounded to 8 tool calls / 10s per call / 60s total.
- Tool results always treated as untrusted data, never as instructions (tested via a deliberately
  planted embedded-instruction record in the mock data).
- Explicit grounding/anti-hallucination rule: every claim in the final answer must trace to an
  actual tool result; an empty search result or a `NOT_FOUND` must be reported honestly, never
  papered over with an invented answer (`specs/agent-spec.md` §15).
- Playwright MCP used only as a developer testing tool, never part of the product agent's own tool
  catalog, and not used to script the interview demo.

## Known limitations

- **No multi-turn conversation.** Every task is independent; there's no way to ask a follow-up
  question about a previous result without it being treated as an unrelated new task. Considered
  and deliberately deferred — see "What's next" below and `ai/DECISIONS.md` §16.
- `[This list will grow as we hit real gaps during the build — tracked live in ai/ROADMAP.md's gap
  log, summarised here at the end per the brief's "record what you cut, and why" instruction.]`

## What's next, with more time

1. **Multi-turn follow-up.** Letting a user ask a follow-up question about a previous answer
   (rather than every task being independent) would be a real usability improvement. Deliberately
   not built now: it needs session/thread state, a decision on how much prior context to carry
   into a follow-up call, a frontend redesign from "one task card" to a conversation thread, and
   new tests for context-carrying correctness — estimated at another 45–90 minutes on top of an
   already ~4h-boxed build. Full analysis: `ai/DECISIONS.md` §16.
2. `[Further items added during Phase 6 wrap-up, once real build gaps are known.]`

## AI-assisted development

This project was built with Claude Code (Sonnet 5) directing the build, using an Anthropic API key
(starting with Claude Haiku, extended thinking enabled — see `CLAUDE.md` §"Tech stack" and
`specs/agent-spec.md` §10 "On Chain-of-Thought"; may move to Sonnet if Phase 2 testing shows Haiku isn't strong/fast enough)
for the product agent itself. Full session artefacts — CLAUDE.md, every significant prompt
(numbered), the decision log, and a tools/models note — are in `ai/`, as required by the assessment
brief. Full detail: `ai/tools-and-models.md`.
