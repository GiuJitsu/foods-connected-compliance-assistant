# Foods Connected — Compliance Assistant

> **Status: living document, Phase 0 + 0.5 (spec + UI mockup) complete, Phase 1 (mock data + MCP server) next.**
> Sections below are written against the spec in `CLAUDE.md` and will be completed/corrected as
> each build phase lands — see `ai/ROADMAP.md` for the phase-by-phase plan and current position.

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

## Use case & MCP service

**Custom, self-built MCP server** over a mock food-supply-chain compliance dataset (suppliers,
certifications, product specifications, quality incidents) — five read-only tools, chosen over
GitHub's public MCP server. Why: thematic relevance to Foods Connected's actual product (grounded
in public research — see `ai/DECISIONS.md` §8), a fully deterministic offline demo (no live-API
flakiness during presentation), and full control to deliberately build in the failure-mode and
untrusted-content scenarios the assessment specifically grades. Full trade-off analysis:
`ai/DECISIONS.md` §5.

## Architecture at a glance

```
mockdata/     — the mock dataset (JSON): suppliers, certifications, specifications, incidents
mcp-server/   — custom MCP server exposing 5 read-only tools over mockdata/
backend/      — Python (FastAPI) API + bounded agent loop (Anthropic API + MCP client)
frontend/     — React + TypeScript UI: task submission, status, tool-activity trace
specs/        — pre-build design specs (MCP tool contracts)
design/       — UI wireframe + functional summary, designed before frontend code exists
ai/           — required submission artefacts: CLAUDE.md context, prompts, decisions, roadmap
```

Full technical spec (entities, tool contracts, agent design, loop bounds, failure handling): see
`CLAUDE.md` (project root) and `specs/mcp-integration-spec.md`.

## How to run

`[TODO — filled in once Phase 1–3 are built. Will include: required environment variables
(ANTHROPIC_API_KEY at minimum), backend/frontend/MCP-server startup commands, and — if a mock model
adapter is ever added — how to toggle it. No mock adapter is currently planned; a real Anthropic
API key is being used throughout, see ai/DECISIONS.md §4.]`

## Key decisions

Full reasoning and chronological log: `ai/DECISIONS.md`. Highlights:
- Custom food-supply-chain MCP server over GitHub's public one — thematic fit + demo determinism.
- Single-shot task model, no multi-turn follow-up — matches the brief's framing, avoids unscoped
  chat-state complexity in a 4-hour build.
- Agent loop bounded to 8 tool calls / 10s per call / 60s total.
- Tool results always treated as untrusted data, never as instructions (tested via a deliberately
  planted embedded-instruction record in the mock data).
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
