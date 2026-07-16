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

## What's next in this summary

Updated again after Phase 1 (mock dataset + MCP server).
