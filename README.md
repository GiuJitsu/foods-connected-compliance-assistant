# Foods Connected — Compliance Assistant

> **Status: living document. Phases 0, 0.5, 1, 2, 3, and 4 (spec, UI mockup, MCP server, backend
> agent loop, frontend, tests) are complete. The frontend is built against the real backend and
> real Anthropic API and verified with a real Playwright browser run — which caught and fixed one
> genuine bug (a React StrictMode polling issue no backend-only test could have found; full account
> `ai/DECISIONS.md` §34). Phases 5 (gap-diagnosis pass) and 6 (wrap-up) remain.** Sections below
> are written against `CLAUDE.md` and `specs/agent-spec.md`, completed/corrected as each build
> phase lands — see `ai/ROADMAP.md` for the phase-by-phase plan.
> Repo: https://github.com/GiuJitsu/foods-connected-compliance-assistant

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

**Backend (Phase 2 — runnable today):**
```
cd backend
pip install -r requirements.txt
set ANTHROPIC_API_KEY=your-key-here   (PowerShell: $env:ANTHROPIC_API_KEY = "your-key-here")
python -m uvicorn main:app --reload
```
Then `POST http://localhost:8000/api/tasks` with `{"task": "which dairy suppliers have an expired certification?"}`,
poll `GET /api/tasks/{task_id}` for the result, or `GET /api/info` for the static info panel. Full
contract: `CLAUDE.md` §"Backend API contract". No mock model adapter is planned; a real Anthropic
key is used throughout (`ai/DECISIONS.md` §4) — without one set, task submission will fail with a
`MODEL_API_FAILURE`/`INTERNAL_ERROR`, not a crash (the tests use `FakeModelClient` instead, no key
needed: `cd backend && pip install -r requirements.txt && python -m pytest`).

**Frontend (Phase 3 — runnable today):**
```
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` — expects the backend running at `http://localhost:8000` (override
with a `VITE_API_BASE_URL` env var if it's elsewhere). React + TypeScript + Vite; see
`frontend/README.md` for the component layout.

**Frontend end-to-end tests (Playwright, dev-only — `ai/DECISIONS.md` §9):**
```
cd frontend
npx playwright install chromium   # first time only
npx playwright test
```
Requires both the backend and frontend dev servers already running (see above), plus a real
`ANTHROPIC_API_KEY` for the one test that submits a real task.

**Running the tests:**
```
cd mcp-server && pip install -r requirements.txt && python -m pytest
cd backend && pip install -r requirements.txt && python -m pytest
```
Both run entirely against fake models/fake tool sets by default — no network calls, no spend. One
file, `backend/tests/test_real_llm_integration.py`, is the exception: it calls the real Anthropic
API and the real MCP server, and is automatically skipped unless `ANTHROPIC_API_KEY` is set (so a
routine run never spends money by surprise).

**What's tested — 33/33 passing, matching the brief's coverage target (1 happy path + 2–3 failure
scenarios + 5–6 validation edge cases, `CLAUDE.md` §"Testing requirements") plus additional coverage
beyond that minimum:**

| Category | Where | Count |
|---|---|---|
| Happy path | `test_agent_loop_happy_path.py` | 1 |
| Failure scenarios — MCP unreachable / tool error mid-task / model-API failure | `test_agent_loop_failures.py` | 3 |
| Validation edge cases E1–E6 (empty result, zero-cert supplier, invalid enum, embedded-instruction text, allergen boundaries, expiry boundary) + NOT_FOUND contracts | `mcp-server/tests/test_edge_cases.py` | 10 |
| Loop-bound enforcement (iteration cap, total timeout) | `test_loop_bounds.py` | 2 |
| Duplicate-call safety net | `test_dedup.py` | 1 |
| Anti-hallucination grounding backstop | `test_grounding.py` | 4 |
| HTTP API contract | `test_api.py` | 5 |
| Real MCP protocol (fake model + the real server, real stdio) | `test_real_mcp_integration.py` | 3 |
| True end-to-end (real HTTP → real agent loop → real MCP server, polled to completion) | `test_end_to_end_http.py` | 1 |
| Real Anthropic API + real MCP server, both genuinely live | `test_real_llm_integration.py` | 3 |

All `backend/tests/` paths above are relative to `backend/tests/`. Per-test rationale and the full
run transcript: `ai/test-log.md`.

**Frontend (Playwright, dev-only — not part of the product agent's own tool catalog):** 13 tests
in `frontend/tests/`, all passing — 4 against the real backend + real MCP server + real Anthropic
API (`e2e.spec.ts`: info panel, client-side validation, a full real task, dark mode), and 9 against
a schema-accurate mocked backend for states a real run can't reliably force on demand (`e2e-mocked-
states.spec.ts`: all 3 `FAILED` sub-reasons, both `limit_hit` types, grounding-`FLAGGED`, all 4
tool-error categories together, the auto-clearing question field). One real bug was found and fixed
this way — a React `StrictMode` polling issue invisible to every other test in this project, since
none of them involve a browser at all. Full account: `ai/DECISIONS.md` §34.

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
- Playwright used only as a developer testing tool, never part of the product agent's own tool
  catalog, and not used to script the interview demo. Originally planned to run as an MCP server
  (per the brief's own tool-shape); when no Playwright MCP server turned out to be connected in this
  build session, installed the `@playwright/test` **package** directly instead — same verification
  value (a real Chromium browser), no MCP wrapper needed. Full account: `ai/DECISIONS.md` §34.

## Known limitations

- **No multi-turn conversation.** Every task is independent; there's no way to ask a follow-up
  question about a previous result without it being treated as an unrelated new task. Considered
  and deliberately deferred — see "What's next" below and `ai/DECISIONS.md` §16.
- **In-memory task store.** `backend/main.py` keeps tasks in a plain Python dict — fine for a local
  single-process demo (no persistence requirement anywhere in the brief), but restarting the backend
  loses all task history, and it wouldn't survive multiple backend instances.
- **Grounding backstop catches ID-shaped hallucination only.** `backend/grounding.py` regex-matches
  `SUP-`/`CERT-`/`SPEC-`/`INC-` prefixed tokens against tool results — it cannot catch a fabricated
  *fact* about a real entity (e.g. inventing a certification date for a real supplier) or a
  name-only hallucination with no ID attached. Explicitly scoped this way from the start, not
  discovered late — full rationale `specs/agent-spec.md` §17.
- **Some frontend states verified via a mocked backend, not a forced real failure.** The 3 `FAILED`
  sub-reasons, the limit-hit path, and grounding-`FLAGGED` are proven to render correctly given a
  schema-accurate payload (`frontend/tests/e2e-mocked-states.spec.ts`) — that the *backend* actually
  produces each of those states is proven separately, but not together in one single real run (doing
  so on demand — e.g. forcing a real model API failure — isn't reliably reproducible). Recorded
  honestly in `ai/ASSESSMENT-CRITERIA.md` rather than overclaimed.
- **No CI pipeline.** All 46 automated tests (33 backend/mcp-server + 13 frontend) are run manually
  from the command line, not on every push. Fine for a single-developer 4-hour assessment; a real
  gap for anything longer-lived.
- **Single browser, no accessibility audit.** Playwright testing used Chromium only; no cross-browser
  pass and no screen-reader testing, beyond the basic choices already in place (focus-visible states,
  a considered color palette, semantic HTML).

## What's next, with more time

1. **Multi-turn follow-up.** Letting a user ask a follow-up question about a previous answer
   (rather than every task being independent) would be a real usability improvement. Deliberately
   not built now: it needs session/thread state, a decision on how much prior context to carry
   into a follow-up call, a frontend redesign from "one task card" to a conversation thread, and
   new tests for context-carrying correctness — estimated at another 45–90 minutes on top of an
   already ~4h-boxed build. Full analysis: `ai/DECISIONS.md` §16.
2. **CI pipeline.** A GitHub Actions workflow running `mcp-server/`, `backend/`, and `frontend/`
   tests on every push — the tests already exist and pass locally, this is purely wiring.
3. **Fact-level grounding, not just ID-level.** A second, cheap model call that checks the final
   answer's factual claims against the tool results actually gathered, catching hallucinations the
   regex-based backstop structurally can't (see "Known limitations" above).
4. **Persist task history** to a real datastore so the trace survives a backend restart, and so a
   user could browse past tasks, not just the one currently on screen.
5. **Cross-browser and accessibility pass** — Firefox/Safari via Playwright's other browser projects,
   and a real screen-reader pass, not just the structural accessibility choices already made.

## AI-assisted development

This project was built with Claude Code (Sonnet 5) directing the build, using an Anthropic API key
(Claude Haiku, `claude-haiku-4-5-20251001`, extended thinking enabled — see `CLAUDE.md` §"Tech
stack" and `specs/agent-spec.md` §10 "On Chain-of-Thought") for the product agent itself. Confirmed
empirically against the real API (`ai/test-log.md`) that Haiku's tool-selection and
grounded-answering quality is sufficient — no move to Sonnet needed. Full session artefacts —
CLAUDE.md, every significant prompt (numbered), the decision log, and a tools/models note — are in
`ai/`, as required by the assessment brief. Full detail: `ai/tools-and-models.md`.
