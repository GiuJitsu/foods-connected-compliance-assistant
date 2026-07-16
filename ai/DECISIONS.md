# Decisions Log — Food Connected AI Engineering Assessment

Chronological record of scope, design, constraints, rules, goals, and intended results. Each entry
is a locked decision (or an explicitly open question). This file is the source of truth if a
session is interrupted or context is compressed — read this file top-to-bottom to resume with full
context. Conclusions live here; day-to-day narrative reasoning can be reconstructed from
`prompts.md` if more detail is ever needed.

Status tags: `LOCKED` (decided, don't revisit without new information), `OPEN` (needs a decision),
`PROVISIONAL` (working assumption, flagged for confirmation).

---

## RESUME POINT (updated at every meaningful step, per P17 — read this first)

**Rewritten clean at P30, updated at P31, P35, P36, P40** — this block had drifted stale (stacked
"next" notes from several rounds back, contradicting itself). Superseded content below is gone, not
archived — history for each of these is in its numbered §, not here.

**Where we are:** Phases 0, 0.5, 1, 2, 3, and 4 are all **DONE**. Phase 3 (`frontend/`, React +
TypeScript + Vite) was designed as an approved Artifact mockup first, then built against the locked
API contract, then verified with a real Playwright browser run against the real backend + real
Anthropic API — which found and fixed one genuine bug (a React StrictMode polling issue, §34) no
other test in this project could have caught. Only Phase 5 (closed-loop gap-diagnosis pass) and
Phase 6 (wrap-up) remain. Prompt count: P1–P40 logged in `ai/prompts.md`.

**Tools installed this session that weren't present at the start:** Python 3.12 (P18), git + gh
(P19), Node.js LTS (P39), `@playwright/test` + Chromium (P40, installed as an npm package since no
Playwright MCP server was actually connected — `ai/DECISIONS.md` §34).

**What exists and works, concretely:**
- `CLAUDE.md` — full project spec, Tier-3 standard, includes the Backend API contract (§ added P29).
- `specs/agent-spec.md` — single, complete product-agent spec (identity → validation → assumptions,
  §1–§17), including the grounding rule + mechanical backstop and the LLM-vs-Python responsibility map.
- `specs/mcp-integration-spec.md` — full MCP tool contracts + trace schema (incl. `INTERNAL_ERROR`,
  locked model id, `grounding_check`).
- `prompts/system_prompt.txt` — the literal system prompt, loaded directly by `backend/`.
- `mcp-server/` + `mockdata/` (Phase 1) — built and verified twice: tool logic directly, and the
  real MCP stdio protocol end-to-end (real handshake/list_tools/call_tool).
- `backend/` (Phase 2) — FastAPI app: bounded agent loop, trace recording, grounding backstop,
  R2/R5 dedup safety net, swappable fake/real model+MCP clients. Built via an actual closed-build-loop
  pass (fresh subagent, three-part build prompt) and independently re-verified: 19/19 tests pass,
  including 3 real-MCP-protocol integration tests. 5 real spec gaps found and fixed — full log:
  `ai/build-loop-fix-log.md`.
- `design/ui-mockup/` — wireframe + functional notes, ready for Phase 3 to build against.
- Git: local repo + GitHub remote, public, pushed through commit `187741a` (7 commits total).
- `README.md`, `ai/ASSESSMENT-CRITERIA.md`, `ai/ROADMAP.md`, `ai/tools-and-models.md` all current
  as of this checkpoint.

**Standing rules currently active (all in `CLAUDE.md`, don't re-derive, just follow):** print
roadmap status every step; confirm before creating new artefact/doc files (code files in Phases
1–3 exempt, announce layout instead); log every prompt verbatim without being asked; keep this
Resume Point current without being asked; commit + push at every important step; run an Integrity
Check periodically (one has run — §21).

**Immediate next action:** Phase 3 — frontend (React + TypeScript + Vite), built against the
acceptance criteria AC1–AC15 in `CLAUDE.md` and the API contract now locked there, using
`design/ui-mockup/wireframe.svg` as the visual reference. Announce the file/module layout before
scaffolding (per the code-files exemption, no per-file confirmation needed).

**Known open items (full list: §20):** visual polish for Phase 3, sequenced after functional ACs,
first thing to cut if time is tight. (Model tier and MCP-server edge-case-test coverage were both
open items here — both resolved at §32, see Resume Point above.)

---

## 0. Source documents

- `2026 AI Engineering Assessment.pdf` (project root) — the assessment brief. Full text captured
  in this session; key points summarised in §1 below.
- `AI FDE Training/` — a separate training-program repo the user completed before this exercise.
  **We do not write inside this folder.** It's read-only reference material.
- `AI FDE Training/Reference/` — contains the ATX methodology docs (`atx/atx-concepts.md`,
  `atx-scoring.md`, `atx-assessment.md`, `atx-agent-mapping.md`, `atx-economics.md`) plus
  `claude-md-examples-guide.md`, `production-spec-checklist.md`,
  `spec-ambiguity-vs-builder-mistakes.md`, `integration-spec-template.md`,
  `discovery-questioning-patterns.md`, `Thinking-Discipline-Primer.md`, and capstone materials.

## 1. Assessment requirements summary — LOCKED

**Goal:** Web app where a user submits a natural-language task; a Python backend runs a **bounded
agent loop** (LLM + tools) to complete it; tools are sourced from **at least one MCP server**;
a React frontend shows the outcome and the agent's tool activity transparently.

**Hard constraints (both must hold, non-negotiable):**
1. Tools must be consumed **over MCP** — not wired directly into the backend.
2. **Tool selection is the model's decision**, made inside the bounded loop — no hardcoded call
   sequence with the model just summarising at the end.

**Backend must:** expose an API for the frontend; run the agent loop (connect to MCP server,
present tools, execute model-chosen calls, feed results back, support multiple calls per task);
bound the loop (iteration cap + timeouts, at minimum); fail well (unreachable MCP server, mid-task
tool error, model failure → meaningful state, never a hang or stack trace); take secrets from
environment only.

**Frontend must:** let user submit a task and see progress/result; show, per tool call, the tool
name, input, and a summary of the result, such that a user can understand what the agent did and
why the answer is what it is; show sensible failure states.

**Model access:** own API key, mainstream provider, cheap/small model acceptable; mock adapter
allowed only if no API access, and only if paired with an MCP service that itself needs no paid
access.

**Testing:** automated tests "where they earn their place" — agent loop against a fake model/fake
tools (loop bounds, error paths, result handling) is called out as the natural target.

**Deliverables:**
1. Git repo with real history (commits that tell the story, not one final commit).
2. `ai/` directory in the repo: agent instruction files (CLAUDE.md etc.), significant prompts,
   transcripts/session summaries, a note on tools/models used. **Required, not optional.**
3. README: how to run (incl. env vars, mock-adapter toggle if any), use case + MCP choice, key
   decisions, known limitations, what's next with more time.

**Time box:** ~4 hours for someone fluent in this already. Do not substantially exceed. If scope is
cut, record what and why in the README — a deliberate cut is a positive signal.

**What gets assessed:** agent design (prompts/tools/loop bounds/failures); how the system treats
content it can't trust (tool results are untrusted input); codebase quality as production code;
frontend transparency (does it faithfully show what the agent did); how AI tools were directed and
verified (artefacts + commit history + presentation); judgement over feature tour.

**Presentation (15 min + Q&A):** use case & MCP choice and why; agent design (system prompt, tool
presentation, loop bounds, failure handling); how the build itself was AI-directed; what the AI got
wrong and how it was caught.

## 2. What from ATX methodology is actually useful here — REVISED (see §7)

ATX is built for enterprise consulting engagements (client discovery, business-case scoring,
economics). Most of it doesn't apply — there's no client, no real workload, no ROI case to build.
What transfers:

- **Five elements of an enterprise agent** (Purpose, Scope, Context, Tools, Governance) from
  `atx-agent-mapping.md` — used as the checklist for the agent design section of CLAUDE.md and the
  system prompt.
- **Agent Purpose Document shape** (objectives, KPIs/success criteria, failure modes, escalation
  triggers, autonomy — what the agent decides alone vs. escalates) — maps directly onto what the
  assessment asks us to present about agent design.
- **`production-spec-checklist.md`** — buildability bar (no vague "should"/"handle appropriately",
  every conditional has explicit criteria, every integration has timeout/retry/rate-limit/fallback
  defined). Used as the acceptance bar for CLAUDE.md and any capability specs we write before
  building.
- **`spec-ambiguity-vs-builder-mistakes.md`** — the 4-category failure taxonomy (Spec Ambiguity /
  Builder Misread / Test Problem / Design Gap). Used live during the build to diagnose anything
  Claude Code gets wrong, and directly answers the presentation's "what did the AI get wrong, how
  did you catch it" prompt.
- **`claude-md-examples-guide.md`** — the Tier-1/2/3 quality example. CLAUDE.md for this project is
  written to the Tier-3 standard (concrete entities, explicit rules, no generic boilerplate).
- **Two-file context pattern** from the root `AI FDE Training/CLAUDE.md` (CLAUDE.md = concise
  locked rules/decisions, session-log.md = full reasoning trail) — adapted here as
  `CLAUDE.md` (root, rules) + `ai/DECISIONS.md` (this file, decisions + enough narrative to resume
  a session).

**Not used:** volume×value scoring, TCO/ROI modelling, discovery interview patterns, delegation
archetype scoring for a business process — no client, no real process to score.

**Correction, see §7:** this section originally undersold the closed-build-loop discipline itself
(as opposed to the business-scoring machinery) — §7 has the fuller, corrected picture.

## 3. Working agreements with the user — LOCKED

- Don't assume — ask before locking in non-obvious decisions.
- Step by step: after any file is created/edited, state what changed. Substantive design decisions
  wait for confirmation; routine artefact bookkeeping (`ai/DECISIONS.md`, `ai/prompts.md`,
  `ai/ROADMAP.md`) is kept current proactively, without needing a reminder each time (P5).
- Never write inside `AI FDE Training/` — that's read-only reference material from a separate
  training program.
- Project root is `c:\Food Connected demo` (referred to as "Food Connected Demo").
- Every significant prompt from the user gets logged verbatim, numbered, in `ai/prompts.md`.
- This file (`DECISIONS.md`) is updated immediately whenever a decision locks, so progress survives
  context compression — treat it as the resume point.
- `CLAUDE.md` lives at the **project root** (not inside `ai/`) so Claude Code auto-loads it as the
  project constitution during the actual build. The `ai/` directory holds the submission artefacts
  (`prompts.md`, `DECISIONS.md`, and later a session-summary note) — CLAUDE.md is referenced from
  there rather than duplicated, since the assessment's `ai/` requirement is satisfied by pointing to
  the root file plus keeping copies of its historical versions if it changes materially.
- **At every step, print the current `ai/ROADMAP.md` phase table and our position in it, on
  screen** (P7) — not just kept in files.

## 4. Model access — LOCKED

User has an **Anthropic API key**, usable independently of the Claude Code subscription. Backend
agent will call the Anthropic API directly (model tier TBD — likely Haiku or Sonnet for cost, to be
decided when we design the agent loop and estimate call volume per task).

## 5. Use case & MCP server — LOCKED

**Decision:** custom, self-built MCP server over a mock food-supply-chain dataset (suppliers,
product certifications, recalls, allergens) — not the GitHub MCP server.

**Why:** thematically relevant to Foods Connected's actual business (differentiates the submission
from the assessment's own worked example); fully offline/deterministic for the live demo (no
external API flakiness during presentation); full control over the dataset means we can
deliberately engineer genuine multi-tool reasoning (a single question forces 2–3 chained tool
calls) and deliberately engineer the untrusted-content / failure-mode scenarios the brief grades
explicitly, rather than hoping GitHub's live data produces good demo moments. Traded off against
GitHub MCP's lower build effort — accepted the extra build time as worthwhile given what it buys
on the criteria the brief actually scores (agent design story, transparency, failure handling).

**Not chosen — GitHub MCP server:** official, zero build effort, real live data, but generic
(matches the brief's own example almost verbatim), needs a second secret (GitHub PAT), and its
large tool catalog would need curation anyway.

Concrete tool list and dataset shape were refined against real research — see §9.

## 6. Files created so far

- `ai/prompts.md` — prompt log (P1–P14 logged).
- `ai/DECISIONS.md` — this file.
- `CLAUDE.md` (root) — full Tier-3 rewrite, plus P7/P9/P10 follow-ups.
- `ai/ROADMAP.md` — build sequence adapted from the ATX closed-build-loop pattern (§7), Phase 0.5 added.
- `ai/ASSESSMENT-CRITERIA.md` — self-assessment checklist traced to the brief's grading criteria.
- `specs/mcp-integration-spec.md` — full MCP tool contracts (§12).
- `specs/agent-spec.md` — tool-selection rules, delegation boundaries, validation/assumptions (§22).
- `README.md` — purpose, user handbook, brief-required sections (§14).
- `design/ui-mockup/wireframe.svg` + `design/ui-mockup/NOTES.md` — UI mockup + functional summary (§17), renamed from README.md to NOTES.md (§18).
- `ai/tools-and-models.md`, `ai/session-summary.md` — remaining `ai/` deliverable artefacts (§18).

## 7. ATX methodology, revisited — LOCKED

User pushback (P5): ATX is fundamentally about scope definition, task decomposition, and delegation
rules, and the user's own Week 1–5 artefacts encode a decisional process worth reusing, not just a
generic framework. Correct — §2 above undersold it. A background research agent surveyed the actual
weekly folders (`Week1-exercise/`, `Week2-Exercise/`, `Week4/`, `Week5/`) and confirmed a concrete,
reusable pattern (full detail in `ai/ROADMAP.md`):

- **The closed-build-loop artifact sequence is real and consistent across weeks**: a spec/CLAUDE.md
  build brief, followed by numbered artifacts (`01-Test-Cases.md` → `02-Agent-Output.md` →
  `03-Test-Results.md` → `04-Gap-Diagnosis.md` → `05-Fix-Log.md`), diagnosing every gap against the
  4-category taxonomy (Spec Ambiguity / Builder Misread / Test Problem / Design Gap) from
  `AI FDE Training/Reference/spec-ambiguity-vs-builder-mistakes.md`.
- **A verbatim three-part build prompt** is reused across weeks: *"Begin building the agent
  described in this document. First, tell me what you can build confidently without asking
  questions. Second, tell me what you need to clarify before building the rest. Third, build the
  parts you are confident about."* — worth reusing here when a spec is handed off for building.
- **Week 5's integration-spec sub-files** (`07a`/`07c`) and **Agent Purpose Document**
  (`04-agent-purpose.md`) are strong applied templates: the integration specs pair a reference
  implementation with an explicit error/retry table and a "what this does NOT do" section (near
  1:1 fit for our MCP tool contracts); the Agent Purpose Document's four-bucket autonomy matrix
  (decides alone / acts-then-notifies / proposes-human-approves / human-takes-over) plus
  severity-ranked failure modes is the structure adopted for our own agent-design section.

**Decision:** compress this discipline into one spec (this CLAUDE.md) and one running gap log,
rather than the multi-day multi-file version built for a 4-day capstone. Full compressed roadmap:
`ai/ROADMAP.md`. §2 above stands corrected — the process discipline (not the business-scoring
machinery) is the useful part, and it's now the backbone of how we sequence the actual build.

## 8. Foods Connected — real business domain research — LOCKED

Public web research (no client data, no confidential information — all from Foods Connected's own
public marketing site and public company-profile aggregators):

Foods Connected is a cloud-based supply chain management platform for the food industry, used by
150+ manufacturing factories and 8,000+ suppliers across North America, Europe, and Asia-Pacific.
Five solution areas: **Compliance & Food Safety** (supplier audits, compliance workflows, risk
assessments), **Procurement** (e-negotiations, forecasting, cost modelling), **Quality Management**
(real-time quality insights, audits, incident logging), **Product Lifecycle Management** (NPD,
"accurate controls on product specifications in real time"), **Traceability** (end-to-end product
journey tracking via a centralised ledger).

Sources:
- [Foods Connected — homepage](https://www.foodsconnected.com/)
- [Food Compliance Software & Food Supply Chain Management Software](https://www.foodsconnected.com/solutions/food-compliance-software/)
- [Our Solutions — Foods Connected](https://www.foodsconnected.com/solutions/)
- [Food Traceability Software — Foods Connected](https://www.foodsconnected.com/solutions/food-traceability-software/)

**Implication for our mock dataset:** refine the entity names and vocabulary to mirror the real
product areas directly (Compliance & Food Safety + Quality Management + Product Lifecycle
Management — the three areas a lightweight demo can plausibly cover; Procurement and the full
cryptographic Traceability ledger are out of scope, too complex for a 4h build). Revised entity
model, replacing the earlier placeholder from §5:

- **Supplier** — id, name, country, category, risk_rating. (mirrors "supplier risk management")
- **Certification** — supplier_id, standard (BRCGS / GLOBALG.A.P. / ISO 22000 / SALSA — real food
  safety certification schemes), status (VALID/EXPIRED/SUSPENDED), expiry_date. (mirrors
  "supplier audits... risk assessments")
- **Specification** — id, supplier_id, name, category, allergens[], status (DRAFT/APPROVED/
  UNDER_REVIEW). Named "Specification," not "Product" — this is Foods Connected's own term
  ("accurate controls on product specifications").
- **Quality Incident** — id, specification_id, date, type (RECALL/COMPLAINT/NON_CONFORMANCE),
  severity, description. (mirrors "log incidents to improve product quality")

Tool list from §5 is renamed to match (`search_specifications` not `search_products`,
`search_quality_incidents` not `search_recalls`) but otherwise unchanged in shape/count (5 tools).
Full spec goes in `CLAUDE.md` and `specs/mcp-integration-spec.md`.

## 9. Playwright MCP — LOCKED (both roles)

**Playwright MCP is a tool for Claude Code during development only.** Used to drive a browser and
exercise the React frontend end-to-end once it exists. Explicitly **not** part of the in-app
product agent's own tool catalog; that agent only ever gets the custom food-supply-chain MCP
server. Keeping the two separate avoids muddying the assessment's core requirement (the product's
agent loop reasoning over food-compliance tools) with an unrelated browser-automation tool that has
nothing to do with the chosen use case.

**No scripted interview demo.** User agreed (P7) with the recommendation: don't script the
interview demo with Playwright. The brief explicitly rewards judgement over "a feature tour" and
asks the candidate to walk through what the agent did and why — a human narrating a live,
manually-driven demo shows understanding more directly than a script running itself, and a
scripted demo adds live-presentation risk (if it desyncs or breaks, there's no fallback) for no
grading benefit the brief asks for. The demo is presented live/manually.

**Best use of Playwright found:** a small Playwright-driven E2E test (happy path + one failure
case), added to the automated test suite if time allows (Phase 4/5) — legitimately satisfies the
brief's testing section and is a good talking point for "how you verified your AI tools."

## 10. New tracking artefacts — LOCKED

- `ai/ROADMAP.md` — phase-by-phase build sequence (spec → MCP server → agent loop → frontend → one
  closed-loop gap-diagnosis pass → wrap-up), time-budgeted against the ~4h box, adapted from the
  closed-build-loop pattern in §7.
- `ai/ASSESSMENT-CRITERIA.md` — every grading criterion and deliverable from the brief, tracked as a
  checklist, to self-assess against before submission.

## 11. Product agent design decisions — LOCKED (confirmed P8)

Set while writing the full CLAUDE.md rewrite, under the latitude given in P5 ("keep writing... without
needing reminders"), clarified in plain language in chat, and explicitly confirmed by the user in
P8 ("Keep all four"):

- **Interaction model: single-shot, not multi-turn chat.** The agent runs one task to completion (or
  explicit partial/failure) per submission; it cannot ask a mid-task clarifying question. Chosen
  because the brief frames the flow as "user submits a task ... backend completes it," and building
  real clarification round-trips wasn't judged worth the scope cost in a 4-hour build.
- **Loop bounds:** iteration cap = 8 tool calls/task; per-tool-call timeout = 10s; total task
  timeout = 60s. Arbitrary-but-reasonable defaults for a 5-tool catalog where a realistic query
  chains 2-3 calls; easy to retune once we see real tool-call patterns in testing.
- **Escalation ranking** (5 failure modes, most-to-least likely) — see CLAUDE.md
  §"Product agent design" for the full list.
- **Three deliberate test fixtures** (embedded-instruction supplier record, one reserved
  supplier_id that simulates a tool timeout, one guaranteed-empty query) — required by CLAUDE.md's
  domain data model section, to be built into the mock dataset in Phase 1.

## 12. P7 follow-up decisions — LOCKED

- **Roadmap-status visibility:** at every step, print the current `ai/ROADMAP.md` phase table and
  our position in it, on screen, in chat — not just kept in files. Added to `CLAUDE.md` working
  agreements.
- **Detailed MCP spec:** `specs/mcp-integration-spec.md` written using the shape of
  `AI FDE Training/Reference/integration-spec-template.md` (11-section REST template adapted to 5
  MCP tool contracts) — full version; the compact table in `CLAUDE.md` stays for quick reference
  during the build.
- **Mock data location:** own top-level `mockdata/` folder, separate from both `mcp-server/` (the
  server code) and `backend/` — not nested inside either.
- **Testing scope, agreed explicitly:** 1 happy path + 2–3 failure scenarios + 5–6 validation edge
  cases, with the mock dataset built to make every one of them genuinely reproducible (not just
  asserted in a test without backing data). Full breakdown in `CLAUDE.md` §"Testing scenarios &
  required mock data" — only one of the three failure scenarios (mid-task tool error) is
  data-dependent; the other two (MCP server unreachable, model/API failure) are test-harness-level
  faults, not something the dataset itself encodes.
- **Playwright — fully agreed** (§9 updated from OPEN to LOCKED on both the dev-tool role and the
  no-scripted-demo call).

## 14. P8 follow-up: single-shot semantics, transparency requirements, README — LOCKED

**Single-shot, confirmed:** yes — one task submission runs the loop to completion; there is no
follow-up turn that continues the same reasoning context. The user can submit a *new*, independent
task afterward, but it starts fresh with no memory of the prior task. Documented as a named
limitation (not a hidden gap) in `README.md`'s "known limitations" / "what's next" sections.

**8-call cap scope, confirmed:** yes — it's per single-shot task. Within one submission, the agent
autonomously decides which of the 5 MCP tools to call, with what arguments, and in what order, up
to 8 calls total, before it must stop and answer.

**Transparency requirements, strengthened.** User asked whether "what data is being used, what MCP
tools are called, what calls error, whether any limit was hit" is already covered in
`ai/ASSESSMENT-CRITERIA.md`. It was covered generally (F3/F4/A4) but not spelled out explicitly
enough to build against directly. Fixed by:
- Adding a dedicated "Frontend transparency requirements" section to `CLAUDE.md` enumerating
  exactly what the UI must render (task text, overall status, full ordered tool-call trace with
  per-call success/error detail, an explicit iteration-cap/timeout-hit indicator, final vs. partial
  answer distinction, distinct displays for each of the three failure modes).
- Adding a task-level `limit_hit` field (`NONE` / `ITERATION_CAP` / `TIMEOUT`) to the trace schema
  in `specs/mcp-integration-spec.md` §10, alongside the existing per-call fields — so "was a limit
  hit" is a first-class, explicit signal, not something the frontend has to infer.
- Adding `ai/ASSESSMENT-CRITERIA.md` row F6 for limit-hit visibility specifically.

**New artefact:** `README.md` (project root) — purpose overview + end-user handbook (how to read
the transparency UI) + the brief's required README sections (use case/MCP choice, key decisions,
known limitations, what's next). Created as a living document now, completed as phases land.

## 15. P9 follow-up decisions — LOCKED

- **UI acceptance criteria (AC1–AC9) + a textual wireframe** added to `CLAUDE.md`
  §"UI interaction design & acceptance criteria" — designed now (spec-first, cheap on paper),
  built in Phase 3 only once Phases 1–2 (mock data/MCP server, backend agent loop) are solid, since
  the frontend depends on the backend's trace/status contract existing first.
- **Phase 3 gets its own scoped closed-build-loop pass using Playwright**: build the UI against
  AC1–AC9, drive it with Playwright, diagnose any gap with the 4-category taxonomy, fix. Confirmed
  this only happens after foundations (Phases 1–2) are solid, per the user's explicit caveat.
- **Validation/error taxonomy added to the trace schema**: `error.type` ∈
  `[VALIDATION_ERROR, NOT_FOUND, TIMEOUT, SERVER_ERROR]`, not just a success/fail boolean — user's
  "UI could also show validation (if successful or not)" point. Updated in
  `specs/mcp-integration-spec.md` §10 and `CLAUDE.md` §"Frontend transparency requirements."
- **CLAUDE.md scope clarified in the file itself** (not just in chat) — a short note now sits under
  the file's opening explaining what belongs in CLAUDE.md (build-relevant requirements: entities,
  contracts, agent/UI rules) vs. `ai/ASSESSMENT-CRITERIA.md` (external grading checklist),
  `ai/DECISIONS.md` (reasoning/history), `ai/ROADMAP.md` (phase sequencing). Assessment: current
  CLAUDE.md is on the right side of this line already — no restructuring needed, just made explicit
  for future readers (and it's a good presentation talking point: deliberate separation of
  concerns).

## 16. Multi-turn follow-up — LOCKED (P10: "let's leave as is")

User asked whether follow-up queries (instead of strict single-shot) would be nicer for the user
and how much complexity it would add. Analysis given in chat:

**What it would require:** session/conversation state (a thread ID, task history stored server-side);
deciding how much prior context to carry into a follow-up call (full tool-call history vs. just
prior final answers — risk of unbounded context growth across many turns); a frontend redesign
from "one task, one card" to a conversation thread view; new test surface (context-carrying
correctness, follow-up ambiguity resolution); a decision on whether loop bounds (§"Loop bounds")
apply per-turn only or need a session-level cap too.

**Estimate:** meaningfully more work — realistically another 45–90 minutes on top of an already
~3.5–4.5h budget, real risk of exceeding the brief's "do not substantially exceed ~4h" instruction.

**Decision, confirmed P10:** keep single-shot for the build. Multi-turn follow-up is now recorded
as item #1 in `README.md` §"What's next, with more time," with the complexity estimate carried
over verbatim. Closed — do not revisit without new information (e.g. spare time genuinely
materialising late in the build).

## 17. P10 follow-up decisions — LOCKED

- **UI mockup created**: `design/ui-mockup/wireframe.svg` (visual wireframe — five zones: static
  info panel, task input, status banner, tool-call trace, final answer) + `design/ui-mockup/NOTES.md`
  (functional summary: what the app is, what it looks like, what a user can do, and a full table
  mapping every transparency question to where it's answered in the UI).
- **Transparency requirements expanded** (user's explicit list: which tools called, what data
  retrieved, what processing/synthesis happened, what reasoning the model applied — plus items we
  suggested): added a per-call `reasoning` field (short, model-stated rationale for that specific
  tool call — captured from the assistant text preceding the tool_use block, deliberately *not* raw
  chain-of-thought), a task-level "basis line" (call success/fail counts, model name, total time), a
  static always-visible "how this agent works" info panel (model/tools/limits), and a "view raw
  trace JSON" affordance. Added to `CLAUDE.md` §"Frontend transparency requirements" (now 8 items)
  and §"UI interaction design & acceptance criteria" (AC10–AC13 added, 13 total), the trace schema
  in `specs/mcp-integration-spec.md` §10 (`reasoning`, `model`, `total_duration_ms` fields), and
  `ai/ASSESSMENT-CRITERIA.md` (row F7).
- **Roadmap updated**: new Phase 0.5 ("UI mockup & functional summary") inserted between Phase 0
  and Phase 1, marked done; Phase 3's acceptance-criteria reference updated to AC1–AC13.

## 18. P11 follow-up decisions — LOCKED

- **Extended thinking: enabled, shown (Option B).** Reversed the earlier decision to exclude raw
  chain-of-thought. User's pushback was correct: the reason not to show it as *authoritative* is a
  reason to *caption it carefully*, not to *hide it* — hiding it worked against the brief's own
  "as explicit and transparent as possible" instruction. Now: extended thinking is enabled on the
  Anthropic API calls; shown per tool-call step behind a collapsed-by-default disclosure with a
  fixed caption ("the model's own unedited reasoning for this step — not guaranteed to be a
  complete or authoritative account of why it acted"); the curated `reasoning` one-liner stays
  inline and always visible regardless. Trade-off accepted knowingly: extra output tokens + latency
  per call, in tension with choosing Haiku for cost — to be calibrated for real in Phase 2, not
  guessed at now. `CLAUDE.md` §"On chain-of-thought", trace schema `thinking` field in
  `specs/mcp-integration-spec.md` §10, AC14 added, `ai/ASSESSMENT-CRITERIA.md` row F8.
- **Folder structure confirmed at repo root.** `ai/` stays scoped to session artefacts per the
  brief's literal deliverable #2 wording (CLAUDE.md pointer, prompts, session summary, tools/models
  note); `specs/`, `design/`, and `README.md` stay at repo root — `specs/`/`design/` are product
  design docs, not AI-session artefacts, and README is the brief's own separate deliverable #3
  (also needs to be root-level for GitHub/GitLab to auto-render it). User confirmed this reading.
- **Naming collision fixed.** User noticed two files named `README.md` (root, and inside
  `design/ui-mockup/`) — legitimate confusion about which one is "the" deliverable. Renamed the
  subfolder one to `design/ui-mockup/NOTES.md`; all cross-references updated (`CLAUDE.md`,
  `README.md`, `ai/ROADMAP.md`, the SVG's own footer text).
- **Deliverable-tracking gap closed.** User asked where all deliverables are tracked — answer:
  `ai/ASSESSMENT-CRITERIA.md` §"Deliverables" (D1–D11), mapped directly to the brief's 3 numbered
  deliverables. Checking it surfaced two genuinely missing items (not just unstarted — actually
  not yet created): D4 (transcripts/session summaries) and D5 (tools/models note). Fixed
  immediately: `ai/session-summary.md` (living, D4) and `ai/tools-and-models.md` (D5) created.

## 19. P12/P13 correction — LOCKED

User caught an overstatement: §18 framed `ai/session-summary.md` as closing a "missing deliverable"
gap. Re-checked the brief's exact wording — *"the significant prompts you used, transcripts **or**
session summaries"* — an *or*, not an *and*. `ai/prompts.md` (verbatim, numbered) already satisfies
this as a transcript; it was never actually missing. `ai/tools-and-models.md` remains genuinely
required (the brief lists "a brief note on which tools and models" as its own separate item, and
nothing else in the repo does that job specifically) — that one stands as originally reasoned.

`ai/session-summary.md` also legitimately overlaps in content with this very file (same events,
prose instead of a decision log). **Resolution, confirmed P13:** keep it, but re-labelled from
"deliverable" to **presentation-prep material** — a narrative easier to talk from than a stack of
numbered decisions when covering "how you directed your AI tools" / "where you intervened" in the
15-minute presentation. `ai/ASSESSMENT-CRITERIA.md` D4 updated to point at `ai/prompts.md` as the
actual satisfying evidence, not `ai/session-summary.md`.

**Pattern worth naming:** this is the second time a user question has caught me stating something
as more load-bearing/required than it actually was (first: treating some CLAUDE.md defaults as if
already decided before they were confirmed, P7→P8; now: overstating a file as deliverable-required
when it wasn't). Worth being more careful to distinguish "required per the brief" from "a good idea
we're choosing to do" when presenting new files going forward.

## 21. Integrity Check #1 (P14) — run and fixed

First run of the Integrity Check procedure defined in `CLAUDE.md` §"Integrity Check." Re-read every
artefact fresh rather than trusting memory of writing them. Findings and resolution:

**Fixed directly (objective corrections, no design judgement needed):**
- Two broken cross-references: `DECISIONS.md` §2 pointed to "§8" twice when it meant §7 (both now
  fixed); `ROADMAP.md`'s own compression-rationale pointer had the same §8→§7 bug.
- §13 ("Open questions") was physically out of numeric order (sat after §19) — renumbered to §20,
  now at the true end.
- `ai/prompts.md` prompt-count references were stale ("P1–P10") — corrected to P1–P14.
- `ROADMAP.md` Phase 3 still said "AC1–AC13" after AC14 was added to `CLAUDE.md` — synced.
- `limit_hit` enum was lowercase in `CLAUDE.md`/`DECISIONS.md` prose, uppercase in the actual
  schema — violated CLAUDE.md's own naming-convention rule; standardised to uppercase everywhere.
- `design/` folder was missing from `CLAUDE.md`'s own "Repository layout" section — added, along
  with the `ai/` file list catching up to reality (`tools-and-models.md`, `session-summary.md`).
- Wireframe SVG mislabeled "completed — limit hit" as a "failure state" in its own section heading,
  contradicting CLAUDE.md's explicit statement elsewhere that limit-hit is not one of the three
  failure modes — heading corrected.
- `specs/mcp-integration-spec.md` forward-referenced a future `mockdata/README.md` — would have
  recreated the exact naming collision from §18. Changed to `mockdata/NOTES.md` pre-emptively.
- Entity count targets were only specified for Supplier — added a target table for all four
  entities to `CLAUDE.md`, sized to actually support every test scenario in §"Testing scenarios."

**Fixed with a proposed resolution (real design gap, applied but flagged as overridable):**
- `COMPLETED_PARTIAL` was underspecified — the spec promised exactly 4 UI states including
  "completed with limit hit," but the wireframe's own worked example showed a *different* partial
  outcome (a failed tool call, no limit hit) with no defined status for it. Resolution applied:
  `COMPLETED_PARTIAL` fires for either cause; `limit_hit` (which can legitimately be `NONE`)
  distinguishes which. Never silently shown as plain `COMPLETED` when the answer is actually
  incomplete. Applied to `CLAUDE.md` (2 places) and `specs/mcp-integration-spec.md` §10.
- Missing system-prompt requirement: nothing said the model must be explicitly instructed to state
  a reason before each tool call — without it, `reasoning` would likely be empty in practice,
  silently breaking AC10. Added a "System prompt must-haves" note to `CLAUDE.md`.

**Flagged, resolved P15:** scope of the P14 "confirm before creating files" rule — confirmed
artefact/documentation files only (`ai/`, `specs/`, `design/`, root docs). Routine implementation
code in `mockdata/`, `mcp-server/`, `backend/`, `frontend/` during Phases 1–3 is exempt; instead,
the file/module layout is announced at the start of each phase so there's a chance to object before
a batch of code lands, not a per-file confirm. `CLAUDE.md` §"Working agreements" and §"What Claude
Code should NOT do" updated accordingly.

## 22. P16 — tool-selection rules & specs/agent-spec.md — LOCKED

User question: does the agent have any rules for *how* it chooses tools, beyond "the model
decides," and where should such rules live? Real gap — CLAUDE.md specified bounds and escalation
but never tool-selection strategy. Six rules established (search-before-guessing an ID, no
redundant calls, stop when sufficient, respect dependency order, never retry a deterministic
failure, recognise multi-target tasks) — full detail with acceptance criteria in `specs/agent-spec.md`.

**Document placement, decided:** user chose a new file (`specs/agent-spec.md`) over folding into
`CLAUDE.md`, mirroring the existing compact-in-CLAUDE.md/full-in-specs pattern already used for
the MCP integration spec — and asked it be written to `production-spec-checklist.md`'s discipline
(testable acceptance criteria, explicit delegation boundaries, validation design, assumptions
register), same standard already applied to `specs/mcp-integration-spec.md`.

**`reasoning`-reliability, strengthened.** User asked whether we could "maximise" the chance the
`reasoning` field always appears — proposed and applied a stronger mechanism: `reasoning` is now a
**required input parameter on all 5 MCP tools**, schema-enforced (missing/empty → `VALIDATION_ERROR`
like any other missing required field), not just a system-prompt request. This is strictly
stronger than the P14/Integrity-Check-#1 fix (system-prompt instruction alone) — that instruction
stays as a second layer, but the schema requirement is what actually guarantees it. Verified this
doesn't weaken hard constraint #2: the model still freely chooses *which* tool and its domain
arguments; `reasoning` is an additional required argument, not a constraint on the choice itself
(explicit check in `specs/agent-spec.md` §4). Updated: all 5 tool schemas in
`specs/mcp-integration-spec.md` §4, the trace-schema provenance note in §10, `CLAUDE.md`'s MCP tool
contracts table and system-prompt-must-haves section, `ai/ROADMAP.md` Phase 0.

## 23. Phase 1 kickoff: schema-first approach, and a real gap caught while implementing — LOCKED

**User question (P17):** any other opportunity to establish formal schemas/structured data before
building? **Answer: yes, and the ordering matters.** Rather than writing `mockdata/*.json` freehand
against CLAUDE.md's prose entity tables and hoping it matches, Phase 1 writes **Pydantic models
first** (`mcp-server/schemas.py`) — one model per entity (Supplier, Certification, Specification,
QualityIncident) plus one input model per MCP tool (matching `specs/mcp-integration-spec.md` §4
exactly, including the required `reasoning` field). These models are then the actual validation
mechanism for the mock data (each JSON record is loaded through its Pydantic model, which fails
loudly on any mismatch) — not just documentation of intent. Chosen over a separate prose "data
schema" spec file because Pydantic models double as runtime code (FastAPI and the MCP server both
consume Pydantic natively) — one artefact serves as both the formal schema and the implementation,
rather than a spec file that could drift from the code the way a couple of Integrity Check findings
already showed prose/schema can drift from each other.

**Real gap caught applying this discipline, immediately:** writing the Pydantic `Supplier` model
against CLAUDE.md's own entity table surfaced that E4's fixture ("Supplier's notes-style field
contains embedded instruction-like text") has nowhere to live — Supplier has no free-text field in
the spec. Classified via the 4-category taxonomy: **Design Gap** — the spec was clear about what it
said, but silent on where the field actually was, because it was never checked against the entity
model that was supposed to support it. Fixed by moving the fixture to `QualityIncident.description`,
which already exists and is arguably more realistic (an incident description is more plausibly
untrusted free text than a supplier profile field). `CLAUDE.md` E4 and `specs/mcp-integration-spec.md`
§11 updated. This is a concrete, presentation-worthy example of the closed-build-loop discipline
catching a real gap during implementation, not just during planning.

## 24. Phase 1 code written and verified — LOCKED

Wrote `mcp-server/schemas.py` (Pydantic models), `mockdata/*.json` (4 files: 18 suppliers, 20
certifications, 25 specifications, 10 incidents), `mcp-server/server.py` (FastMCP-based server, 5
tools), `mcp-server/requirements.txt`.

**No Python interpreter existed in this dev environment** — checked `python`/`python3`/`py`; only
a Windows Store execution-alias stub was present. User chose (P18) to install Python here via
winget rather than defer verification or install elsewhere. Installed **Python 3.12.10** via
`winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements
--accept-source-agreements`. PATH doesn't auto-refresh within an already-running PowerShell
session (shell state doesn't persist across tool calls here either), so subsequent commands used
the direct interpreter path.

**Actually verified this time, not just reviewed:**
- `pip install -r mcp-server/requirements.txt` succeeded (mcp, pydantic, and their dependencies).
- `schemas.py` imports and validates all 4 mock data files cleanly (18/20/25/10 records).
- `server.py` imports cleanly and loads all data.
- Every tool function called directly and produced the exact designed output: `search_suppliers`
  happy path (IT dairy suppliers); `get_supplier_profile` happy path with certs; `NOT_FOUND` on an
  unknown supplier; the E2 zero-certification supplier (SUP-017) returns an empty list, not an
  error; the E3 invalid-enum case (`category: "CHEESE"`) returns a clean `VALIDATION_ERROR`; a
  **blank `reasoning`** correctly triggers `VALIDATION_ERROR` — the structural-enforcement design
  from §22 actually works, confirmed, not just argued for; the E1 empty-result-set case returns
  `{"results": [], "count": 0}`; `check_allergen_conflicts` correctly detects a GLUTEN conflict on
  SPEC-019 and correctly `NOT_FOUND`s an unknown specification.
- The `SUP-TIMEOUT-01` fixture measured at **12.0s elapsed**, confirmed longer than the 10s
  per-call timeout budget (`CLAUDE.md` §"Loop bounds") — the fixture will correctly trip a real
  timeout once Phase 2's backend enforces that bound.

**Update (P25) — the stdio transport gap above is now closed.** User correctly pushed back on
language in a later summary ("the MCP server is already running") that implied more than had
actually been checked at the time — the distinction between "the Python functions work" and "a
real MCP client can connect to this over the protocol and call them" is real, and I'd let it blur.
Verified properly: a scratch script (`mcp.client.stdio.stdio_client` + `mcp.ClientSession`) spawned
`server.py` as a subprocess exactly as a backend would, ran the real MCP handshake (`initialize`),
called `list_tools` (all 5 tools returned correctly), and called `call_tool` twice over the actual
JSON-RPC protocol — once a happy-path `search_suppliers` call, once with a blank `reasoning`,
correctly rejected with `VALIDATION_ERROR` **at the protocol layer**, not just in a direct function
call. This is now genuinely verified, not just argued to be probably fine.

## 25. Git repository + GitHub — IN PROGRESS

User (P19) asked for a git repo with commits at every important step and a GitHub remote, and
(P20) confirmed: exclude `AI FDE Training/` entirely (it's separate, unrelated training material,
not part of this submission — including ~14,900 unrelated files would bury the actual codebase);
GitHub auth handled by the user running `gh auth login` interactively themselves, then confirming
back, since `gh auth login`'s browser/token flow can't run inside a non-interactive tool call.

**Done:**
- Installed **Git 2.55.0** and **GitHub CLI 2.96.0** via winget (same pattern as Python — no git/gh
  existed in this environment either).
- Set global git identity: `Giuseppe <giuseppe.ardito@gmail.com>` (P21).
- `.gitignore` created: excludes `AI FDE Training/`, secrets (`.env*`), Python/Node build noise,
  and `.claude/` (Claude Code's local permission settings — found while checking `git status` for
  the first time; it's machine-local tooling config, not project source, so excluded on the same
  reasoning as everything else that isn't "the codebase").
- `git init` at the project root.
- Two commits made: (1) all spec/design/tracking artefacts as of repo creation — `CLAUDE.md`,
  `specs/`, `design/`, `README.md`, `ai/*`, the PDF; (2) the verified Phase 1 implementation —
  `mcp-server/`, `mockdata/`. Not a single final commit, and not fake fine-grained history either —
  two honest logical units reflecting real separation (spec vs. verified implementation), with
  future commits landing incrementally from here as real work happens.

**Still open:** user needs to run `gh auth login` and confirm; then `gh repo create` (name/visibility
TBD — ask when this comes up) + push.

## 26. Agent spec fully consolidated into specs/agent-spec.md — LOCKED

User pushback (P22): the CLAUDE.md/agent-spec.md compact/full split — which worked well for the
MCP integration spec — made agent *behaviour* harder to understand, not easier, since
understanding "how does the agent decide and act" requires identity, scope, bounds, rules, and
failure handling together, not two files stitched together mentally. Agreed (P23): fully
consolidate into `specs/agent-spec.md`.

**Moved out of `CLAUDE.md` entirely, now living only in `specs/agent-spec.md`:** Identity &
Purpose, Interaction Model, Scope, Loop Bounds, Untrusted Content Handling, System Prompt
Must-Haves (merged with the existing Reasoning-Capture Mechanism section), Escalation/Failure
Behaviour, On Chain-of-Thought, What the Product Agent Should NOT Do. `CLAUDE.md` §"Product agent
design" is now a 2-paragraph pointer with three "quick facts" (loop bounds, delegation, untrusted
content) for readers who don't need the full depth.

**Also added while consolidating (P22, "is there no systematic decision-making?"):** a
**Tool-Selection Decision Flow** — the same 6 rules (R1–R6), now also framed as an ordered
5-step check the agent runs each iteration (is the task answerable? → does the next step need an
ID? → does it imply multiple targets? → would this repeat/retry a call? → otherwise make the next
closing call). This doesn't add any hardcoded sequencing (would violate hard constraint #2) — it
orders the *considerations*, not the *tool choice*, which stays the model's judgement call.
`specs/agent-spec.md` §5.

Every cross-reference to the moved sections was updated across `CLAUDE.md`,
`specs/mcp-integration-spec.md`, `README.md`, `ai/ASSESSMENT-CRITERIA.md`,
`ai/tools-and-models.md`, and `design/ui-mockup/NOTES.md` — checked via grep, not assumed correct
(the pattern from Integrity Check #1's reference-issue findings). Historical entries in this file
(§11, §12, §14, §18, earlier) were **not** rewritten — they're accurate records of what was true
when written (content was in `CLAUDE.md` at the time), not live pointers.

## 27. P24 — grounding rule, system prompt draft, README expansion, sync checklist, UI polish — LOCKED

Five items in one prompt; handled together, recorded together.

**1. Anti-hallucination / grounding rule (real gap, now fixed).** User asked how we prevent the
model from hallucinating when data isn't available. The data layer already returns clean empty
results (`count: 0`) and explicit `NOT_FOUND` errors, but nothing told the *model* what to do with
them — a real gap, not just an oversight, since an empty array is exactly the kind of thing a model
can paper over with an invented answer. New `specs/agent-spec.md` §15: every claim in the final
answer must trace to an actual tool result; empty/`NOT_FOUND` results must be reported honestly.
Added as validation edge case 6 + failure mode 4 (§12) and assumption A4 (§13, flagged as the
highest-severity assumption in the register — undetected hallucination directly undermines the
brief's trust requirement).

**2. System prompt: when/where, answered.** User asked whether `specs/agent-spec.md`'s
requirements-checklist (§8) is sufficient, or whether the literal prompt text needs writing, and
when. Answer: the checklist alone isn't enough — the brief explicitly wants the system prompt
covered in the presentation, so a literal, usable draft now exists (`specs/agent-spec.md` §16),
written now as part of the spec rather than deferred to Phase 2, so Phase 2 wires it in directly.
Expected to be refined once Phase 4 shows real model behaviour, not treated as final.

**3. README expanded**: "What you can ask" (6 concrete example questions, including one
deliberately zero-result question to invite testing the grounding rule), "Available data" (real
counts now that Phase 1 exists: 18/20/25/10), "MCP server & tools" (documents Phase 1 is built and
verified, lists all 5 tools plainly), "How to run" updated with real, runnable commands for the MCP
server (backend/frontend still `[TODO]`, honestly).

**4. "When do we start building the MCP server?" — clarification, not a new decision.** This was
already done and verified in Phase 1 (§24) before this prompt; the user's question suggested it
hadn't registered as complete. Answered directly in chat rather than assuming the question implied
a design change, and used it as the trigger to fix the real, related gap: `README.md` didn't yet
document that it was built, which is a legitimate documentation gap regardless of the question's
premise.

**5. "Files to keep in sync" checklist added to `CLAUDE.md`** (per "make sure claude contains
reference to templates and files to update during the process") — a table of every tracked file
and when to touch it, plus an explicit list of the `AI FDE Training/Reference/` templates this
project's specs were built from, so both are scannable in one place rather than scattered across
`ai/DECISIONS.md` history.

**6. UI visual-quality item added** to `ai/ROADMAP.md` Phase 3 and `CLAUDE.md` §"Visual quality" —
sequenced explicitly *after* AC1–AC14 (functional/transparency criteria), and named as the first
thing to cut deliberately if the time box is tight, consistent with the brief's own grading
emphasis (functional transparency and agent design over visual polish) while still taking "quality
and consistency of the codebase" seriously if time allows.

All committed and pushed together as one logical unit (§25 pattern continues).

## 28. P25/P26 — MCP protocol actually verified; system prompt relocated — LOCKED

**MCP protocol overstatement, corrected and then actually fixed.** User caught real overstated
language ("the MCP server is already running") — the gap between "functions work directly" and "a
real MCP client can connect over the protocol" had been correctly flagged once (§24) but then blurred
in later summaries. Rather than just re-flagging it, closed it for real: a scratch script
(`mcp.client.stdio.stdio_client` + `mcp.ClientSession`) spawned `server.py` as a subprocess exactly
as a backend would, ran the actual MCP handshake, `list_tools` (5 tools confirmed), and `call_tool`
twice over real JSON-RPC — a happy path and a blank-`reasoning` rejection, both correct at the
protocol layer. `README.md`, `ai/ASSESSMENT-CRITERIA.md` C1, and `ai/DECISIONS.md` §24 updated with
precise language distinguishing "tool logic verified" from "protocol verified" going forward.

**System prompt relocated to its own folder** (P25/P26, user's explicit request + confirmed
mechanism): new `prompts/system_prompt.txt` — raw text, no markdown, directly loadable by Phase 2
(`open(...).read()`). `specs/agent-spec.md` §16 is now a pointer + rationale, not a second copy of
the text — same lesson as the CLAUDE.md/agent-spec.md consolidation (§26): one source of truth,
not two files to keep in sync by hand. `CLAUDE.md` repository layout and "files to keep in sync"
table updated; `README.md` architecture diagram updated.

## 29. P27/P28 — LLM/Python responsibility map + grounding mechanical backstop — LOCKED

User asked to confirm the architecture split ("system prompt directs the LLM part, Python handles
the deterministic part") — correct, formalised as a full table in `specs/agent-spec.md` §17 rather
than left as an informal understanding. Surfacing this map exposed one real, previously-accepted
gap: grounding (§15) was prompt-only, no code-side enforcement, unlike `reasoning` (which has a
hard Pydantic gate). Asked the user directly rather than deciding unilaterally whether to close it
now or defer to Phase 4 validation — **user chose to close it now** (P28).

**Grounding mechanical backstop, designed** (`specs/agent-spec.md` §17): after the loop produces a
final answer, regex-extract ID-shaped tokens (`SUP-`, `CERT-`, `SPEC-`, `INC-` prefixes matching
`mockdata/`'s actual ID conventions) and flag any not present in the task's own trace. New
`grounding_check` field on the task-level trace object (`specs/mcp-integration-spec.md` §10):
`status: PASSED|FLAGGED` + `unrecognized_references`. Does **not** change task `status` — kept as
an independent trust signal, not conflated with completion state.

**Explicitly documented limits, not oversold:** catches invented *entities* (the primary failure
mode named in §15), not hallucinated *facts* about real entities, and not name-only hallucinations
(names aren't reliably regex-matchable). A full semantic fact-check was considered and explicitly
scoped out — real token cost (needs another model call), not worth it for a 4h build. Assumption A4
(§13) updated to reflect partial closure, not full closure — prompt-layer effectiveness on
hallucination *attempts* (as opposed to catching them after the fact) is still a Phase 4 empirical
question.

**New AC15** (grounding warning shown in UI) + **F9** in `ai/ASSESSMENT-CRITERIA.md` + Phase 2's
`ai/ROADMAP.md` row updated to include building this backstop. Caught and fixed my own mistake
mid-edit: a `replace_all` meant to update the live AC1–AC14→AC15 references also silently rewrote a
*historical* line in `ai/ROADMAP.md` (Phase 0.5's record, correctly AC14 at the time) — reverted
that one specifically. Worth naming as a recurring risk: `replace_all` is convenient but blind to
the historical-vs-live distinction this file's own discipline depends on.

## 30. P29 — closed build loop run for real on Phase 2 — LOCKED

User asked to run the training program's own closed-build-loop process (three-part build prompt,
review the three outputs, log gaps, fix them) rather than have me build Phase 2 directly. Ran it
properly: a fresh subagent with **no conversation history** — not me — was given only the 5
build-facing spec files (`CLAUDE.md`, `specs/agent-spec.md`, `specs/mcp-integration-spec.md`,
`prompts/system_prompt.txt`, the already-verified `mcp-server/`) and explicitly told not to read
`ai/DECISIONS.md`/`ai/prompts.md`/`AI FDE Training/`, so any real gap would surface as a genuine
question, not something found by reading our own history.

**Operational note:** the first dispatch appeared interrupted by the user before starting, but had
actually already begun running in the background and completed — `backend/` existed on disk before
the second dispatch, which correctly reviewed/verified rather than blindly rewrote it. Everything
below is independently re-verified by me (full test suite re-run myself, `agent_loop.py` /
`grounding.py` / `main.py` / `schemas.py` / `config.py` read directly), not taken on the
subagent's word — "trust but verify" applied literally here, not just claimed.

**Result: 19/19 tests pass, including 3 real-MCP-stdio-protocol integration tests. Code faithfully
matches the spec** (loop bounds, trace schema, dedup safety net, grounding backstop all correct) —
no drift beyond the 5 gaps below. Nothing was genuinely blocked (the "what it could not build"
output was empty, correctly — the Anthropic client is fully built, just not exercised against the
live API per the environment constraint given).

**Gap log — full detail in `ai/build-loop-fix-log.md`, summarised here:**
1. API endpoint contract never specified anywhere (Design Gap) → ratified the builder's sensible
   choice, locked into `CLAUDE.md` §"Backend API contract".
2. Exact model id never locked, only given as an illustrative example (Spec Ambiguity) → **fixed
   with real information the fresh builder had no way to know**: `claude-haiku-4-5-20251001` is
   the actual current id. This is exactly what the closed-build-loop discipline is for — a fresh
   builder correctly refuses to guess; the spec-writer (with more context) resolves it.
3. `FailureReason` enum missing a bucket for a genuine internal bug, was being folded into
   `MODEL_API_FAILURE` (Design Gap) → added `INTERNAL_ERROR`, updated `backend/schemas.py` and the
   exception handler in `backend/agent_loop.py`.
4. `COMPLETED_PARTIAL` semantics — "otherwise" in §9 #2 was genuinely ambiguous about whether
   partial fires only on unrecovered failures (Spec Ambiguity) → locked the stricter reading (any
   failure → partial, regardless of apparent recovery) as official, no code change — the backend
   already implemented the safer interpretation.
5. `thinking` attribution when one turn has multiple tool calls (Design Gap, borderline Acceptable
   Variation) → ratified the builder's choice (shared thinking copied to every entry in that turn)
   as correct, documented explicitly, no code change.

All spec files updated to match (`CLAUDE.md`, `specs/agent-spec.md` §9, `specs/mcp-integration-spec.md`
§10), tests re-run and still 19/19 passing after the 2 code changes. `ai/ROADMAP.md` Phase 2 marked
DONE; `ai/ASSESSMENT-CRITERIA.md` C1/C2, all of B1–B9, and most of the Testing section moved from
TODO to DONE with real evidence, not just marked complete.

## 31. P31 — testing scope clarified, roadmap tidied, stale deliverable statuses fixed — LOCKED

User asked three things: (1) tidy `ai/ROADMAP.md` from Phase 4 onward; (2) should tests cover the
agent/Python code too, not just the MCP server, and should they go true end-to-end from submission
to result; (3) does `README.md` already explain what can be queried and what data is available.

**Testing scope, locked:** not MCP-only. Three layers already exist and are correctly separated —
agent-loop logic (fake model + fake MCP, 16 tests), real MCP wiring (fake model + the real MCP
server over actual stdio, 3 tests), and HTTP contract (FastAPI `TestClient`, loop stubbed). The
real gap, restated precisely: (a) `mcp-server/` has **zero** automated tests — E1–E6 were only ever
manually verified in Phase 1; (b) no test currently exercises the *whole* stack — HTTP submission →
real `run_task()` → poll to terminal state → assert the trace — because the existing API tests stub
the loop and the existing loop tests never go through HTTP. Both added to `ai/ROADMAP.md` Phase 4 as
concrete, named line items. **Deliberately not adding**: an automated test against the real
Anthropic API — cost and flakiness on every run; real-model verification stays a manual, one-off
check, explicitly recorded as a deliberate cut rather than left unstated.

**README check:** already covers this, no gap. §"What you can ask — examples" (6 concrete example
questions spanning single-lookup and multi-tool-chain queries) and §"Available data" (entity
counts, categories/countries/statuses, what's deliberately fabricated) were both written during the
P24 README expansion. Confirmed by re-reading the file, not assumed.

**Stale statuses found and fixed while doing this** (`ai/ASSESSMENT-CRITERIA.md`): D1 (git repo)
was still `TODO` despite 8+ pushed commits; D2/D3 said `DOING` for artefacts that are substantially
current; D6/D8/D9/D10 (README sections) said `TODO` even though all of those sections were written
during the P24 expansion. Corrected to accurate current status with real evidence pointers, not
left as an unrelated drift for a later Integrity Check to catch.

`ai/ROADMAP.md` Phase 4 row rewritten with the three concrete sub-items above (was a generic
one-liner). Phase 6 row noted README is substantially done already, to revisit for accuracy only.

## 32. P32–P35 — Phase 4 fully built and run, including real-LLM tests — LOCKED

User reversed the P31 "deliberately not adding a real-API test" cut: asked to build and actually
run everything, including against the real LLM, right now.

**Security practice, locked:** the API key was never pasted into this chat or written to any file.
User set it themselves as a persistent Windows user env var (`setx ANTHROPIC_API_KEY "..."` in
their own terminal, outside this session) — the only way for it to reach my PowerShell tool calls
at all, since shell state doesn't persist across separate tool invocations here and a fresh process
only sees a variable set via `setx`/the registry, not one set with `$env:` in a different process.
Verified present by checking the variable's **length only** (`[System.Environment]::
GetEnvironmentVariable('ANTHROPIC_API_KEY','User')`, length-checked, never printed) — consistent
with hard constraint #3 ("secrets come from the environment only, nothing sensitive is ever
committed") applied to the chat/log surface too, not just to git.

**Built (code-file exemption, no per-file confirmation needed — announced layout before writing):**
- `mcp-server/tests/test_edge_cases.py` (10 tests) + `mcp-server/conftest.py` + `mcp-server/pytest.ini`
  + `pytest>=8` added to `mcp-server/requirements.txt` — one test per E1–E6 plus two NOT_FOUND
  contract checks, all against real IDs read directly from `mockdata/*.json` rather than assumed
  (confirmed SUP-017 has zero certs, CERT-020's `expiry_date` is exactly `2026-07-16` — the
  project's fixed "today" — SPEC-008/SPEC-019 are the empty/multi-allergen boundary pair, INC-003
  carries the embedded-instruction text).
- `backend/tests/test_end_to_end_http.py` — real POST → real background `run_task()` (NOT
  stubbed, unlike `test_api.py`) → real MCP subprocess → polled via `TestClient`'s persistent
  background event-loop thread (`with TestClient(...) as client:`, required for the background
  `asyncio.create_task` to actually run between polls) → asserted against the real returned trace.
- `backend/tests/test_real_llm_integration.py` — 3 tests, real `AnthropicModelClient` + real
  `StdioMCPClient`, gated by `pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), ...)` so
  a routine `pytest` run on a keyless machine (or CI) never spends money by surprise — this is a
  deliberately manual, opt-in run, not part of the default suite's cost profile.

**Result: 33/33 tests passed** (10 mcp-server + 23 backend, 3 of which are the new real-LLM tests;
0 skipped this run since the key was present). Full breakdown, evidence, and per-test rationale:
`ai/test-log.md` (new artefact, proposed and created in direct response to the user's explicit
request in this same message — not a unilateral addition).

**Real finding, not just a pass/fail:** the real model (`claude-haiku-4-5-20251001`) correctly chose
tools on its own for both a zero-certifications lookup and a legitimately-empty incidents query, and
reported both honestly — the grounding backstop reported `PASSED` on the empty-result case, meaning
no fabricated ID appeared in the answer. This resolves the standing open question in this file's old
§"Open questions" ("Haiku vs Sonnet ... confirm during build if tool-selection reasoning is strong
enough") — **Haiku is sufficient, no move to Sonnet.**

`ai/ROADMAP.md` Phase 4 marked DONE. `ai/ASSESSMENT-CRITERIA.md` T1/T4 moved TODO→DONE, M1's
evidence pointer extended to the real-LLM test result.

## 33. P36 — post-Phase-4 sync pass across every artefact — LOCKED

User asked to update all relevant files before moving to Phase 3, and where test results are
written. Answered directly: `ai/test-log.md` (added §32) is the single source of truth for test
run results — a human-readable, committed markdown summary, not raw pytest console output (which
isn't persisted anywhere) and not a CI artifact (no CI configured in this project).

Audited every file named in `CLAUDE.md`'s "Files to keep in sync" table against §32's changes and
found real staleness beyond what §32 already fixed:
- `CLAUDE.md` §"Tech stack" and §"Testing requirements" still described Haiku as provisional
  ("may move to Sonnet if...") and testing as forward-looking — both now resolved facts, not open
  items. Fixed, plus a "Last updated" log entry appended (never edited by insertion — this file's
  own append-only-at-tail convention for that section).
- `README.md` status banner and "AI-assisted development" section had the same provisional-Haiku
  language; added a "Running the tests" block to §"How to run" so a reader knows both suites exist
  and that the real-API test is opt-in/gated, not silently skipped without explanation.
- `ai/tools-and-models.md` had the same provisional hedge — fixed with the same real-run evidence.
- `ai/session-summary.md` was the one genuinely stale file: **last touched at Phase 0.5**, with a
  dangling "Updated again after Phase 1" placeholder that was never followed up despite Phases 1, 2,
  and 4 all completing since. Added all three phases' narrative (Phase 3 still pending, so the
  placeholder now correctly points there instead).

Deliberately left alone as correct history, not staleness: `ai/DECISIONS.md` §30, `ai/ROADMAP.md`'s
Phase 2 row, and `ai/build-loop-fix-log.md` all still say "19/19 tests" — that was the true count at
that point in the project and these are dated log entries, not live status claims (same
historical-vs-live distinction noted in this file's earlier entries, e.g. the P24 `replace_all`
near-miss). Confirmed via `grep` across all `.md` files before deciding what to touch, not assumed.

## 34. P38–P40 — Phase 3 (frontend) designed, built, and verified with a real browser — LOCKED

Two-stage process, user-directed throughout: design first as a static Artifact, get explicit
approval, then build.

**Design.** First pass (not itself numbered as a prompt — produced from the locked layout/AC
requirements): a restrained ledger/audit aesthetic — serif labels, indigo accent, hairline rules.
User feedback (P38) was a real pivot, not a refinement: bigger banner, a sidebar, food-specific
colors, a non-office display font. Rebuilt with a genuinely different concept — kraft-paper ground,
tomato-red accent, food-grown semantic colors kept separate from it (basil/wheat/stone/fig-plum/wine
per CLAUDE.md's requirement that every error category read as visually distinct, not just red vs
green), rounded display type instead of the ledger serif, task input embedded in the banner itself
(functional, not decorative), and the static info panel moved into a persistent chalkboard-style
sidebar. Approved as-is (P39) before any component code was written — cheap to iterate on as a
static HTML artifact, expensive to iterate on as React.

**Build.** Node.js wasn't installed (same situation Python was in at session start) — installed via
winget with explicit confirmation first, same pattern as P18. Scaffolded `frontend/` (Vite + React
19 + TypeScript), then built the full component tree against the locked API contract
(`CLAUDE.md` §"Backend API contract") and AC1–AC15: `types.ts` mirrors `backend/schemas.py`
field-for-field, `api.ts`/`hooks/useTask.ts` handle the submit-then-poll-to-terminal-status flow,
and one component per zone (`Banner`, `Sidebar`, `StatusBanner`, `TraceList`, `AnswerCard`,
`FailureCard`). The approved design's CSS tokens/layout were ported directly into `index.css`.
`npm run build` (tsc + vite build) passed clean on the first attempt.

**Verification — the real finding here.** No Playwright MCP server was actually connected in this
session despite `CLAUDE.md`'s plan to use one — `ToolSearch` found nothing. Asked the user how to
proceed (P40); resolved by installing the `@playwright/test` **package** directly into
`frontend/` instead, which lets me drive a real Chromium browser via a script/test file without
needing an MCP tool wrapper at all — and produces a persisted, reusable test suite
(`frontend/tests/e2e.spec.ts`, `frontend/playwright.config.ts`) as a side effect, which
`CLAUDE.md` §"Testing requirements" already called out as a nice-to-have.

Ran the real stack — real backend, real MCP server, real Anthropic API (the key already configured
at §32/§33) — through a real browser. **First run: 3 of 4 tests passed; the real-task test hung and
timed out at 45s with the UI stuck showing "In progress" forever**, even though the backend log
showed the task had actually completed. Root cause, found by reading `useTask.ts` against the
backend log: a classic React 18/19 `StrictMode` double-effect pitfall. The polling hook's cleanup
effect set `mounted.current = false` on unmount but never reset it to `true` on setup — harmless in
production, but `StrictMode` deliberately double-invokes effects in development
(mount → cleanup → mount) specifically to catch bugs like this one, and the cleanup's `false` stuck
permanently after that first simulated unmount. Every subsequent poll's `if (!mounted.current)
return` then fired immediately, silently dropping the result *before* scheduling the next poll —
so after exactly one HTTP request, polling stopped forever, invisibly. Fixed by moving
`mounted.current = true` into the effect's setup phase, not just relying on the initial `useRef(true)`.
Re-ran: 4/4 pass, real task completes in ~9s.

**Why this matters beyond "a bug got fixed":** this class of bug is invisible to every other test in
this project. `backend/tests/` has no React and no browser at all — it could never have caught it.
Only a real browser, actually polling a real backend, surfaced it. This is the concrete answer to
"what did the AI get wrong and how was it caught" (assessment brief presentation point P4) — not a
hypothetical, an actual bug found via the exact tool (Playwright) the spec always intended to use
for this, just wired up a different way than planned once the MCP-server route turned out to be
unavailable in this session.

**What's verified live vs. code-reviewed only:** the happy/partial-completion path, the info panel,
reasoning/thinking disclosure, basis line, raw-JSON view, and grounding-PASSED are all confirmed via
real screenshots of a real run. The 3 FAILED sub-states, the limit-hit path, and grounding-FLAGGED
are implemented and match the same logic already covered by `backend/tests/test_agent_loop_failures.py`
/ `test_loop_bounds.py` / `test_grounding.py`, but weren't separately forced through the live UI —
recorded honestly as `DOING`, not `DONE`, in `ai/ASSESSMENT-CRITERIA.md` F2/F5/F6/F9.

`ai/ROADMAP.md` Phase 3 marked DONE. `ai/ASSESSMENT-CRITERIA.md` F1, F3, F4, F7, F8 moved to DONE;
F2, F5, F6, F9, A4 moved to DOING with the live-vs-code-reviewed distinction stated explicitly.

## 20. Open questions

- ~~Model tier (Haiku vs Sonnet) for the backend agent~~ — **RESOLVED §32**: confirmed empirically
  against the real API, Haiku is sufficient, no move to Sonnet.
- Whether to git-init now or after initial scaffolding — will confirm with user before running
  `git init` since it's a state-changing action worth flagging even though low-risk.
- COMPLETED_PARTIAL semantics (Integrity Check #1, finding 8) — proposed resolution given to user,
  pending confirmation.
