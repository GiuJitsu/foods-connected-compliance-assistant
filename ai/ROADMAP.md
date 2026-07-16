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
| 3 | Frontend | ~45–60 min | Built only once Phases 1–2 are solid (frontend renders the backend's trace/status contract, so it needs that contract to exist and be stable first). Task submission, progress/result display, tool-activity timeline rendered from the trace, failure states — built against the acceptance criteria (AC1–AC15) in `CLAUDE.md` §"UI interaction design & acceptance criteria," using `design/ui-mockup/wireframe.svg` as the visual reference. Verified with a Playwright-driven closed-build-loop pass scoped to the UI: drive each AC, diagnose any gap by the 4-category taxonomy, fix. **Visual polish (added P24):** once AC1–AC15 pass functionally, a pass on visual quality — a real component/design system (not unstyled HTML), consistent spacing/typography/color, basic accessibility (contrast, focus states), responsive layout. Time-boxed: if the ~4h budget is tight, this is the first thing to cut deliberately and record in README "known limitations" — functional transparency (AC1–AC15) takes priority over visual polish, per the brief's own grading emphasis. |
| 4 | Tests — closing the real remaining gaps (added P31 detail) | ~30–45 min | Already **DONE** going in: agent-loop unit/integration tests against fake model + fake MCP (happy path, all 3 failures, loop bounds, grounding, dedup — 16 tests) and 3 real-MCP-stdio-protocol tests (fake model + the *real* `mcp-server/server.py` subprocess). Still **TODO**, three concrete items: (a) `mcp-server/tests/` — direct pytest unit tests against `mockdata/` for every edge case E1–E6 (empty result, zero-cert supplier, invalid enum, embedded-instruction content, allergen boundaries, expiry boundary) — the one layer with zero automated coverage, only manually verified in Phase 1; (b) one true HTTP-level end-to-end test in `backend/tests/` — POST `/api/tasks` with `_run_and_store` **not** stubbed (real `run_task()` + `FakeModelClient` + real MCP server), poll GET to a terminal state, assert the returned trace matches what actually ran — closes the gap where today's API tests stub the loop and today's loop tests never go through HTTP, so nothing currently proves the whole stack works together; (c) **deliberately not adding** an automated test against the real Anthropic API — cost/flakiness on every run, so real-model verification stays a manual one-off check, recorded here as a deliberate cut, not an oversight |
| 5 | One closed-loop gap-diagnosis pass | ~20–30 min | Run the whole thing once end-to-end, classify every real gap hit against the 4-category taxonomy, fix only the highest-leverage ones — no multi-round convergence |
| 6 | Wrap-up | ~15–20 min | README (setup, use case/MCP rationale, key decisions, known limitations, what's next) — **substantially DONE already**, revisit only for accuracy once Phases 3–5 land; final pass on `ai/` artefacts; confirm `ai/ASSESSMENT-CRITERIA.md` is fully checked or has honest "cut, and why" notes |

Total: ~3.5–4.5 hours, matching the brief's "around 4 hours" guidance. If phase 4 or 5 has to be
cut short to stay in budget, that's a deliberate, recordable cut — not a failure — per the brief's
own instruction to cut scope deliberately and say so in the README.

## Gap log (filled in during phase 5)

Format per entry: **Gap** (what happened) → **Category** (Spec Ambiguity / Builder Misread / Test
Problem / Design Gap) → **Fix** (what changed, spec or code).

*(empty — populated during the build)*
