# Build Roadmap

Adapted from the closed-build-loop methodology used throughout `AI FDE Training/` (Weeks 1–5),
compressed for a single ~4-hour build that must produce working code rather than a design-only
deliverable. Full reasoning and evidence for this compression: `ai/DECISIONS.md` §7.

## What we're keeping from the training methodology, and what we're cutting

**Keeping:**
- Spec-first: write the tool/agent contract before writing code, even briefly.
- The closed-build-loop discipline: build, then diagnose every real gap against the 4-category
  taxonomy (Spec Ambiguity / Builder Misread / Test Problem / Design Gap) from
  `AI FDE Training/Reference/spec-ambiguity-vs-builder-mistakes.md`, and fix accordingly — not
  "just patch it and move on."
- The verbatim three-part build framing when handing off a spec-shaped chunk of work: *state what
  can be built confidently, what needs clarifying, then build the confident part.*
- A single running "known gaps" note at the end (Week 5's `BUILD-AMENDMENTS.md` idea), so the
  README's "known limitations" section is accurate, not an afterthought.

**Cutting** (built for a 4-day capstone, not a 4-hour build):
- Separate ADR files, cognitive-load maps, delegation-suitability matrices, multi-pass audit logs.
- Multiple iteration folders with 5+ files each — we use one spec (`CLAUDE.md`) and one gap log
  entry in this file instead.
- Volume×value scoring, economics/ROI modelling — no client, no real workload to score.

## Phases

| # | Phase | Target time | Artefact / output |
|---|-------|-------------|--------------------|
| 0 | Spec | ~15 min | `CLAUDE.md` + `specs/mcp-integration-spec.md` fully filled in: use case, MCP tool contracts (name/input/output/error behaviour), bounded-loop limits, happy-path scenario, failure/escalation scenarios, what the frontend must show for transparency — **DONE**. P16 follow-up: `specs/agent-spec.md` added (tool-selection rules, structural `reasoning`-enforcement design, delegation boundaries, validation/assumptions) — **DONE** |
| 0.5 | UI mockup & functional summary | ~20–30 min | `design/ui-mockup/wireframe.svg` (visual layout reference) + `design/ui-mockup/NOTES.md` (functional summary: what it does, what it looks like, what a user can do); expanded transparency requirements (per-call `reasoning`, final-answer basis line, static info panel, raw-trace-JSON view) folded into `CLAUDE.md` and `specs/mcp-integration-spec.md`; UI acceptance criteria AC1–AC14 written — **DONE** |
| 1 | Mock dataset + MCP server | ~45–60 min | `mcp-server/schemas.py`, `mockdata/*.json`, `mcp-server/server.py`, `requirements.txt` — written **and verified**: Python 3.12 installed, every tool function tested directly (happy path, E1–E3, blank-reasoning rejection, 12s timeout fixture measured). **DONE** |
| 2 | Backend agent loop | ~60–90 min | `backend/` — bounded loop, trace recording, API endpoints (`CLAUDE.md` §"Backend API contract"), `prompts/system_prompt.txt` loaded directly, grounding mechanical backstop, R2/R5 dedup safety net, swappable fake/real model+MCP clients. **Built via a closed-build-loop pass (P29) — a fresh subagent with no conversation history, given only the spec files, ran the three-part build prompt.** 19/19 tests pass (independently re-verified), including 3 real-MCP-stdio-protocol integration tests. 5 real spec gaps found and fixed — full gap→category→fix log: `ai/build-loop-fix-log.md`. **DONE** |
| 3 | Frontend | ~45–60 min | **DONE (P37/P38).** `frontend/` — React + TypeScript + Vite, built against the locked API contract and AC1–AC15. Visual design done as a separate step first (two Artifact design passes, user-directed: v1 a ledger/audit aesthetic, v2 revised to a bigger banner + sidebar + food-market palette per explicit feedback — approved before any code was written). Node.js + Playwright installed this phase (neither present at session start). Verified with a **real** Playwright browser run against the real backend + real Anthropic API (not just fake-model unit tests) — 4/4 tests pass: static info panel loads live tool catalog (AC12), empty-input client-side block (AC1), a full real task end-to-end including the raw-JSON reveal (AC2/AC3/AC5/AC10/AC11/AC13), dark-mode render. **Found and fixed one real bug this way**: a React `StrictMode` double-effect pitfall in the polling hook silently killed all polling after the first tick, leaving the UI stuck on "In progress" forever even though the backend had already finished — undetectable by the backend's own test suite since it has no React/browser involved at all; only a real browser run could catch it. Full account: `ai/DECISIONS.md` §34. **Not yet live-tested**: the 3 FAILED sub-states and the iteration-cap/timeout `COMPLETED_PARTIAL` path (implemented and code-reviewed, matching the same logic already covered by `backend/tests/test_agent_loop_failures.py` and `test_loop_bounds.py`, but not separately forced through the UI). **Visual polish** — done as part of the design-then-build sequence rather than a separate pass after: real design system (CSS custom properties, both themes), no unstyled HTML, focus-visible states, responsive sidebar-to-stack collapse below 860px. |
| 4 | Tests | ~30–45 min | **DONE (P34).** `mcp-server/tests/` — 10 direct pytest unit tests against `mockdata/`, one per E1–E6 plus NOT_FOUND contracts (closes the row that was only manually verified in Phase 1). `backend/tests/test_end_to_end_http.py` — true HTTP-level end-to-end: real POST → real background `run_task()` (not stubbed) → real MCP server subprocess → poll to `COMPLETED`, the one path no other test exercised. `backend/tests/test_real_llm_integration.py` — 3 tests against the **real** Anthropic API + real MCP server (the earlier P31 plan to skip this was reversed at P34: the user asked to run it for real once a key was configured); auto-skips via `pytest.mark.skipif` when no `ANTHROPIC_API_KEY` is present, so a routine run never spends by surprise. **Grand total: 33/33 tests passed.** Full breakdown: `ai/test-log.md`. Confirmed empirically: Haiku's tool-selection and grounded-answering quality is sufficient for this dataset — no move to Sonnet needed, resolving the open question in `ai/DECISIONS.md`. |
| 5 | One closed-loop gap-diagnosis pass | ~20–30 min | **DONE (P41).** 3 real gaps found and fixed, no third round run: (1) Design Gap — the honest `DOING` frontend-state rows from Phase 3 were real, closeable coverage gaps, not just paperwork; closed with `frontend/tests/e2e-mocked-states.spec.ts` (9 new tests: all 3 FAILED sub-reasons, all 3 COMPLETED_PARTIAL reasons, grounding-FLAGGED, all 4 error-category chips together in one screenshot, and the auto-clear field behaviour). (2) Test Problem — 4 of those new tests had ambiguous Playwright locators (self-caught, fixed). (3) Documentation staleness — several `ai/ASSESSMENT-CRITERIA.md` rows (D3, D6, A1, A2, A5) hadn't been flipped from TODO/DOING despite the evidence already existing on disk; fixed. Also: question field now clears itself after submit (small real UX fix, requested alongside Phase 5). Full account: `ai/DECISIONS.md` §35. |
| 6 | Wrap-up | ~15–20 min | **DONE (P42).** Integrity pass across every artefact (found and fixed: several broken `§N` cross-references in the new decisions narrative, a stale "8 new tests" count, `README.md` still claiming Playwright ran as an MCP server when it actually ended up an npm package, `ai/session-summary.md` stale since Phase 0.5). `README.md` "Known limitations" and "What's next" filled in for real (6 limitations, 5 next-steps, no placeholders left). Narrative layer added on top of the raw logs in `ai/prompts.md`, `ai/DECISIONS.md`, and `ai/tools-and-models.md` (now covers every tool/skill used, not just the two models), plus a full presentation script in `ai/session-summary.md` explaining every mechanism (loop bounds, dedup safety net, grounding backstop, structural reasoning validation, untrusted-content handling, failure handling) — purpose, code location, and how each one works. |

Total: ~3.5–4.5 hours, matching the brief's "around 4 hours" guidance. If phase 4 or 5 has to be
cut short to stay in budget, that's a deliberate, recordable cut — not a failure — per the brief's
own instruction to cut scope deliberately and say so in the README.

## Gap log (filled in during phase 5)

Format per entry: **Gap** (what happened) → **Category** (Spec Ambiguity / Builder Misread / Test
Problem / Design Gap) → **Fix** (what changed, spec or code).

*(empty — populated during the build)*
