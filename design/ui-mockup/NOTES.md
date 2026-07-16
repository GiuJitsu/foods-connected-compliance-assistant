# UI Mockup — Functional Summary

> Named `NOTES.md`, not `README.md` — kept distinct on purpose so there's exactly one `README.md`
> in the repo (root), which is the brief's actual deliverable #3. A second file also named
> `README.md` inside a subfolder was flagged by the user (P11) as confusing about which one is
> "the" deliverable; renamed to remove the ambiguity.

Companion to [`wireframe.svg`](wireframe.svg) (open it directly, or view in any browser/image
viewer). This is a layout wireframe, not a visual design pass — it exists to pin down information
architecture and transparency content before any React code is written, per Phase 0/0.5 of
`ai/ROADMAP.md`. Full acceptance criteria this is built from: `CLAUDE.md` §"UI interaction design &
acceptance criteria".

## What the app is

A single-page web app. A user types one natural-language question about a mock food-supply-chain
compliance dataset (suppliers, certifications, product specifications, quality incidents), submits
it, and watches an AI agent answer it — with every step of how it got there shown in full.

## What it looks like (see wireframe.svg)

Five zones, top to bottom:

1. **How this agent works** — a small static info panel (always visible, not per-task): which
   model is answering, which tools it has access to, and the loop's hard limits (8 calls / 60s).
   Costs nothing to build (static text) and is a real transparency win — a user (or an interviewer)
   doesn't have to guess what the agent even is.
2. **Task input** — a text field and submit button. Empty/whitespace-only input is blocked before
   it's sent (AC1).
3. **Status** — one of four visually distinct states: in progress, completed, completed with a
   limit hit, or failed (and failure itself has 3 distinct sub-reasons, see zone 5).
4. **Agent activity** — the full ordered trace of every tool call the agent made. Each entry shows:
   the tool name, the exact input, a one-line **reasoning** note (why the agent chose to call this
   tool — elicited from the model as part of its own tool-calling turn, not fabricated after the
   fact), an expandable **raw extended-thinking** disclosure when the model produced one for that
   step (collapsed by default — see "On chain-of-thought" below), a summary of what came back, and
   success/error — with an explicit **error category** (`VALIDATION_ERROR` / `NOT_FOUND` /
   `TIMEOUT` / `SERVER_ERROR`) when something goes wrong, not just a generic red flag.
5. **Final answer** — visually separated from the trace above it, tagged as complete or partial,
   with a one-line **basis** summary (how many calls succeeded/failed, which model answered, how
   long it took) and a **"View raw trace JSON"** link/button that reveals the exact underlying data
   object for the task (the full schema in `specs/mcp-integration-spec.md` §10, as literal
   formatted JSON) — so nothing in the human-readable cards above is a claim the user has to just
   trust; they can always check it against the real data.

## What a user can do

- Submit one task at a time (no follow-up/conversation memory — see root `README.md` §"Known
  limitations").
- Read, for any completed task, exactly which tools ran, in what order, why (per the agent's own
  stated reasoning, and optionally its full raw thinking for that step), what data came back, and
  how that adds up to the final answer.
- Immediately tell, without digging, whether the answer is complete or partial, and if partial,
  exactly which step failed and why (not just "an error occurred").
- Inspect the raw trace JSON if the human-readable summary isn't enough — the exact data behind
  every card on the page.

## Transparency content — full list

| Question | Where it's answered |
|---|---|
| What MCP tools were called? | Tool name, per trace entry |
| What data was retrieved? | `result_summary` per entry — a concrete summary, not a vague sentence |
| What data processing/synthesis happened? | The final answer's **basis** line (call counts, success/fail split) plus the answer text itself, which is expected to cite what it found |
| What reasoning did the agent apply? | `reasoning` field per trace entry (always visible) **and** the raw `thinking` block when present (expandable, per entry) |
| Which model answered? | Shown in the info panel and in the final answer's basis line |
| What are the agent's limits? | Shown in the static info panel, always visible, not just on failure |
| Was a limit hit, and which one? | Explicit `limit_hit` status, distinct from a normal completion |
| Can I see the unprocessed data? | "View raw trace JSON" link on the final answer |

## On chain-of-thought (resolved P11)

Extended thinking **is shown**, not hidden — reversing an earlier, over-cautious call. It's exposed
per tool-call step, behind a collapsed-by-default disclosure, always captioned: *"the model's own
unedited reasoning for this step — not guaranteed to be a complete or authoritative account of why
it acted."* The short curated `reasoning` line stays inline and always visible regardless; the raw
`thinking` block is the deeper, optional layer underneath it. Trade-off accepted: extended thinking
adds output tokens (cost) and latency per call — a real consideration against Haiku's
cost/speed rationale, and something to calibrate for real once Phase 2 (backend agent loop) is
built and we can see actual latencies against the 60s total-task timeout. Full decision:
`ai/DECISIONS.md` §18.
