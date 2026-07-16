# Session Summary

> Living document — updated as phases complete, finalized during Phase 6 wrap-up. **Not itself a
> required deliverable** — the brief asks for "transcripts **or** session summaries," and
> `ai/prompts.md` (every prompt, verbatim, numbered) already satisfies that as a transcript. This
> file exists instead as **presentation prep**: a narrative account to talk from when covering "how
> you directed your AI tools" and "where you intervened" in the 15-minute presentation — easier to
> present from than `ai/DECISIONS.md`'s numbered decision log, which remains the source of truth for
> reasoning/evidence. Corrected P12/P13 — see `ai/DECISIONS.md` §19.

## Phase 0–0.5: from brief to buildable spec

Started from the assessment PDF and a separate FDE training program's reference material the user
had completed. Read the full brief, then read every file in the training program's `Reference/`
folder (the ATX methodology docs, CLAUDE.md quality-tier guide, production-spec checklist,
spec-ambiguity taxonomy, integration-spec template) to figure out what was actually applicable to a
4-hour coding assessment versus what was built for a different context (enterprise consulting
engagements) and didn't transfer.

Picked a use case by laying out a real trade-off — GitHub's public MCP server (safe, zero build
effort, but generic) versus a custom self-built MCP server (more build time, but thematically tied
to Foods Connected's actual business and fully controllable for demo determinism and deliberate
failure-mode testing). Chose custom, then did real web research on what Foods Connected's product
actually does (Compliance & Food Safety, Quality Management, Product Lifecycle Management,
Procurement, Traceability) and used that to ground the mock dataset's entity names and vocabulary —
"Specification" instead of "Product," real certification-scheme names (BRCGS, GLOBALG.A.P., ISO
22000, SALSA) — rather than inventing something generic.

A background research agent then surveyed the user's actual Week 1–5 training folders and confirmed
a concrete, reusable pattern (numbered build-loop artefacts, a verbatim three-part build prompt, a
4-category gap-diagnosis taxonomy) which became the backbone of `ai/ROADMAP.md`'s phase structure —
compressed from a 4-day-capstone version down to something that fits a single ~4-hour build.

Wrote the full spec: `CLAUDE.md` (Tier-3 standard — entities, MCP tool contracts, product-agent
design, loop bounds, escalation behaviour), `specs/mcp-integration-spec.md` (the same tool
contracts in full, using the training program's own integration-spec template), and
`ai/ASSESSMENT-CRITERIA.md` (every grading criterion and deliverable from the brief, tracked as a
checklist so nothing gets silently dropped).

Iterated on several design points based on user feedback: locked concrete loop-bound numbers (8
calls / 10s per call / 60s total) and a single-shot (no multi-turn) interaction model, explicitly
confirmed after a plain-language walkthrough; added a detailed testing-scenario breakdown (1 happy
path, 2–3 failure scenarios, 5–6 validation edge cases) with the mock dataset designed specifically
to make each one reproducible; agreed Playwright's role is strictly a Claude-Code dev-testing tool,
never part of the product agent's own tool catalog, and never used to script the interview demo.

Designed the UI before writing any frontend code: a wireframe (`design/ui-mockup/wireframe.svg`)
and a functional-summary companion, 14 testable acceptance criteria, and a much more explicit
transparency spec than the first draft — after the user pushed on it twice: once to make "what
data, what tools, what reasoning" concrete rather than implied, and once to reverse an initial,
over-cautious decision to hide the model's extended-thinking content. It's now shown, per tool-call
step, behind a collapsed-by-default disclosure with an explicit non-authoritative caption — a
trade-off knowingly accepted against the cost/latency of Claude Haiku, to be calibrated for real
once Phase 2 exists.

Also corrected a repo-structure question: confirmed with the user that the brief's `ai/` deliverable
is scoped specifically to AI-session artefacts, not the whole project's design docs — `specs/` and
`design/` stay at repo root as product design documents, and `README.md` stays at root as its own,
separate, brief-mandated deliverable. Renamed a subfolder `README.md` to `NOTES.md` once the user
flagged that having two files named `README.md` in the repo was confusing about which one was the
actual deliverable.

## Phase 1: mock dataset + MCP server

Wrote Pydantic schemas (`mcp-server/schemas.py`) before the mock data itself — entity models, a
shared `_ReasoningRequired` base class enforcing every tool's `reasoning` argument structurally
(not just requested in a system prompt), and a reserved timeout-fixture ID. Caught one real spec gap
live while building: the original E4 (embedded-instruction-text) test scenario was written against
"Supplier's notes-style field," but Supplier has no free-text field in the locked domain model —
moved the fixture to `QualityIncident.description`, which already exists and fits the scenario
better (a Design Gap, not a builder mistake — the spec itself was wrong).

Built the 18-supplier/20-certification/25-specification/10-incident dataset to deliberately hit
every required test scenario: a zero-certification supplier (SUP-017), an allergen-empty and an
allergen-heavy specification pair, a certification expiring exactly on the dataset's fixed reference
date, and the planted prompt-injection text in one incident's description. Verified all of it twice:
directly (every tool function called against the loaded data) and — after catching myself
overstating readiness once (P25: said the server was "already running" when only direct Python
calls had been tested, not the actual protocol) — via a real MCP stdio client speaking the actual
protocol to a spawned subprocess.

## Phase 2: backend agent loop, built via a real closed-build-loop pass

Rather than build Phase 2 directly, ran the training methodology's own three-part build prompt for
real: handed a fresh subagent — no conversation history, only the five build-facing spec files, and
explicitly told not to read this project's own decision/prompt logs — the exact instruction *"first
tell me what you can build confidently, second what you need to clarify, third build the confident
parts."* Reviewed all three outputs and independently re-verified the result myself (full test suite
re-run, core files read directly) rather than taking the subagent's report at face value.

Five real gaps surfaced this way, logged gap → category → fix in `ai/build-loop-fix-log.md`: the API
endpoint contract had never been written down anywhere (a fresh builder correctly asked rather than
inventing one — ratified its sensible REST choice); the exact model id had only ever been given as
an illustrative example, so the builder correctly refused to guess a snapshot date, resolved with
real information it had no way to know (`claude-haiku-4-5-20251001`); a genuine internal-bug case had
no `FailureReason` bucket and was being folded into `MODEL_API_FAILURE`, which would have misled a
reviewer into blaming the model for our bug; `COMPLETED_PARTIAL`'s trigger condition had a real
ambiguity about partial recovery, resolved to the stricter reading; and multi-tool-call thinking
attribution needed an explicit, documented choice. This is the closed-build-loop discipline actually
being used as intended, not just described.

## Phase 4: tests, pulled forward and run against the real API

Normally sequenced after the frontend, but the user asked to close every testing gap immediately,
including — after initially agreeing testing the real Anthropic API was a cost/flakiness cut not
worth automating — actually running it for real once a key was available. Built three things: a
`mcp-server/tests/` suite exercising every edge case (E1–E6) directly against the real mock data
(the one layer that had only ever been manually checked); a true HTTP-level end-to-end test that,
unlike the existing API tests, does *not* stub the agent loop — real submission, real background
execution, real MCP subprocess, polled to completion; and `test_real_llm_integration.py`, gated to
skip automatically without a key so a routine run never spends money by surprise.

Handled the API key itself as a security question, not just a config detail: refused to have it
pasted into the chat (it would have been logged verbatim into a file this project pushes to a public
GitHub repo), instead had the user set it as a persistent OS-level environment variable in their own
terminal, and verified it was present by checking only its length, never its value. The real run —
33/33 tests passing — produced an actual finding, not just a green checkmark: the real model chose
its own tools correctly and reported a genuinely empty result honestly rather than fabricating one,
resolving the standing "Haiku vs. Sonnet" question that had been open since Phase 0. Full results:
`ai/test-log.md`.

## What's next in this summary

Updated again after Phase 3 (frontend).
