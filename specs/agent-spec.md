# Agent Spec: Compliance Assistant — Tool-Selection Behaviour

Written to the discipline of `AI FDE Training/Reference/production-spec-checklist.md` (testable
acceptance criteria, no vague "should"/"handle appropriately," explicit delegation boundaries,
validation scenarios, a named assumptions register). This file is the **full** specification of
*how* the agent chooses and sequences tool calls — it does not repeat what's already specified
elsewhere; it points there instead. Compact/summary version and everything else about the agent
(identity, scope, loop bounds, escalation, untrusted-content handling) stays in `CLAUDE.md`
§"Product agent design," the same compact/full split already used for `specs/mcp-integration-spec.md`.

Origin: user question (P16) — "how does the agent decide what tools to call, are there rules we
should establish, and where do they belong?" Answered in `ai/DECISIONS.md` §22.

---

## 1. Purpose

Not repeated at length — see `CLAUDE.md` §"Product agent design" §"Identity & purpose." This file
exists because "the model decides" (hard constraint #2) is necessary but not sufficient: it says
*who* decides, not *how well*. This spec is the *how well* — the rules that shape good tool-calling
behaviour without ever hardcoding a call sequence, which would violate hard constraint #2.

## 2. Delegation Boundaries

**Every tool-selection decision in this build is Agent-Decides-Alone.** There is no human-in-the-loop
step anywhere in the product (§"Interaction model" in `CLAUDE.md`: single-shot, no follow-up, no
mid-task human input) — so the usual four-bucket delegation framework (Agent Decides / Agent
Decides + Logs / Agent + Human Review / Human Decides) collapses to one bucket here by design, not
by oversight. What *is* logged (every call, into the trace) substitutes for human review as the
accountability mechanism — the brief's transparency requirement *is* this build's governance
control, not a missing one.

Not in scope for this agent to ever decide alone or otherwise: any write/mutating action (no such
tools exist — §"MCP tool contracts" in `CLAUDE.md`), and nothing outside the 5 listed tools.

## 3. Tool-Selection Rules

Each rule: statement, explicit trigger condition, and a testable acceptance criterion — per the
production-spec-checklist's BUILDABILITY bar (no "handle appropriately," every conditional has
explicit criteria).

### R1 — Search before guessing an ID
**Rule:** if the task does not name a concrete `supplier_id`/`specification_id`, the agent must
resolve one via the relevant `search_*` tool before calling a tool that requires that ID. It must
never invent or guess an ID string.
**Acceptance criteria:**
- Task "check SUP-014's certifications" (ID given) → `get_supplier_profile("SUP-014", ...)` directly
  is correct; no search call required.
- Task "check Dairy Fresh Ltd's certifications" (name given, no ID) → must call
  `search_suppliers(query="Dairy Fresh Ltd", ...)` first, then `get_supplier_profile` with the
  resolved ID. Calling `get_supplier_profile` with a fabricated ID is a rule violation.

### R2 — No redundant calls
**Rule:** the agent must not call the same tool with materially identical input more than once
within a single task.
**Acceptance criteria:** if `search_suppliers(category=DAIRY, ...)` has already returned results
earlier in the trace, a second identical call within the same task is a rule violation — the agent
must reuse the earlier result.
**Backend safety net (in addition to the rule):** the backend may deduplicate identical
tool+input pairs within a task server-side, returning the cached result instead of re-invoking the
tool — cheap to implement, removes the failure mode entirely rather than just discouraging it. If
built, this is a Phase 2 implementation detail, not a spec change.

### R3 — Stop when sufficient
**Rule:** once the gathered information fully answers the task, the agent must produce the final
answer rather than continuing to call tools "just in case."
**Acceptance criteria:** task "is SUP-001 currently BRCGS-compliant" resolved by one
`get_supplier_profile` call → no further, unrelated calls. This rule is inherently about judgement
quality, not mechanically enforceable server-side (unlike R2/R5) — it's a system-prompt instruction
and a Phase 4 testing spot-check, not a hard gate.

### R4 — Respect dependency order
**Rule:** tools requiring an ID (`get_supplier_profile`, `check_allergen_conflicts`) must only be
called once that ID is known — from the task text itself, or from an earlier tool result in this
task's trace.
**Acceptance criteria:** `check_allergen_conflicts` must never be called with a `specification_id`
that hasn't appeared either in the user's task or in an earlier `search_specifications` result
within the same trace.

### R5 — Never retry a deterministic failure
**Rule:** if a tool call fails with `VALIDATION_ERROR` or `NOT_FOUND`, the identical call must not
be repeated — these fail identically every time (`specs/mcp-integration-spec.md` §5).
**Acceptance criteria:** after `get_supplier_profile("SUP-999", ...)` returns `NOT_FOUND`, a second
identical call within the same task is a rule violation.
**Backend safety net:** same dedup mechanism as R2 could also refuse to re-execute an identical
failed call, returning the cached error instead — optional Phase 2 hardening, not required for
correctness (the rule + system prompt is the primary mechanism).

### R6 — Recognise multi-target tasks
**Rule:** when a task implies checking multiple entities (e.g. "which of our dairy suppliers have
an expired certification"), the agent must check each supplier the relevant search returns —
within the iteration budget — not stop after the first match.
**Acceptance criteria:** task with 3 dairy suppliers returned by `search_suppliers` → the agent
should attempt `get_supplier_profile` for all 3 (budget permitting) before answering; answering
after checking only 1 of 3 without acknowledging the other 2 were skipped is a rule violation.

**What's enforceable server-side vs. system-prompt-only, summarised:**

| Rule | Enforcement |
|---|---|
| R1, R3, R4, R6 | System-prompt instruction + Phase 4 spot-check testing. Judgement-dependent — cannot be mechanically gated without hardcoding a call sequence, which would violate hard constraint #2. |
| R2, R5 | System-prompt instruction + optional backend dedup safety net (Phase 2, if time allows). |
| `reasoning` presence (§4) | Structurally enforced via required tool-input schema — the one rule in this file that *can* be a hard gate without touching hard constraint #2, because it constrains a parameter's presence, not which tool gets called. |

## 4. Reasoning-Capture Mechanism (structural enforcement)

Origin: user question (P16) — "can we maximise the possibility that the reason always appears,
maybe set it as a hard rule?" Resolution: **yes** — `reasoning` is a required string parameter on
all 5 tools' input schemas (`specs/mcp-integration-spec.md` §4), not a hoped-for behaviour elicited
by a system-prompt request alone. A tool call missing or with an empty/whitespace-only `reasoning`
fails server-side with `VALIDATION_ERROR`, the same as any other missing required field — a hard
gate, not a soft nudge. This directly fixes Integrity Check #1 finding 9 (`ai/DECISIONS.md` §21):
the earlier design assumed the model would volunteer explanatory text before a `tool_use` block,
which isn't reliable; a required parameter is enforced by the tool-calling protocol itself.

This does not weaken hard constraint #2 (tool selection is the model's decision) — the model still
freely chooses which tool to call and with what domain arguments; `reasoning` is an additional
required argument alongside the domain ones, not a constraint on the choice itself.

## 5. Validation Design

Per the checklist's minimum bar: at least 1 happy path, 5+ edge cases, 3+ failure modes — scoped
here specifically to tool-selection quality (general agent-loop validation is in `CLAUDE.md`
§"Testing scenarios & required mock data"; this section doesn't repeat that).

**Happy path:** task "which dairy suppliers have an expired certification" → `search_suppliers`
(R1, no ID given) → `get_supplier_profile` per each dairy supplier returned (R6, multi-target) →
each ID sourced from the search result, never fabricated (R4) → no repeated calls (R2) → answer
produced once all suppliers checked, not before (R3).

**Edge cases (tool-selection specific):**
1. Task names a supplier by exact ID already — R1 should *not* trigger an unnecessary search call.
2. Task implies multiple targets but the search returns only 1 result — R6 degenerates correctly
   to a single `get_supplier_profile` call, not an error.
3. Task implies multiple targets and the search returns more suppliers than the remaining
   iteration budget allows — agent must check as many as the budget allows and say so explicitly
   in the final answer (ties to `CLAUDE.md` §"Loop bounds" partial-answer behaviour), not silently
   check only some and claim completeness.
4. A tool call fails with `NOT_FOUND` mid-sequence (e.g. one of several suppliers returns not
   found) — R5 (don't retry that one) combined with R6 (still check the others).
5. Task is fully answerable from the task text alone with no tool call needed — is this realistic
   for this dataset? No — every supported task requires at least one lookup, since the agent has no
   built-in domain knowledge beyond the tool catalog. Flagged here explicitly rather than left
   ambiguous: **zero-tool-call tasks are out of scope for this build's happy path**; if the model
   ever produces a zero-call answer, that's a Phase 4/5 gap to diagnose (likely Spec Ambiguity or
   Builder Misread, per the 4-category taxonomy), not an expected outcome.

**Failure modes (tool-selection specific, beyond the general 3 in `CLAUDE.md`):**
1. Model omits `reasoning` on a call → `VALIDATION_ERROR` (§4) → per R5, must not retry the
   identical call; must supply reasoning and retry, or (if the model can't recover) surface as a
   tool-call failure like any other in the trace.
2. Model fabricates an ID instead of searching first (R1 violation) → the tool call fails with
   `NOT_FOUND` (the fabricated ID won't exist in `mockdata/`) — this is a real, testable way to
   catch an R1 violation in practice: a search-skip shows up as an avoidable `NOT_FOUND`.
3. Model loops on a redundant call (R2 violation) → burns iteration budget without new information;
   testable by checking the trace for duplicate tool+input pairs after a test run.

## 6. Assumptions Register

| # | Assumption | Why it matters | If wrong | Status |
|---|---|---|---|---|
| A1 | Claude (Haiku, extended thinking enabled) reliably supplies a non-empty `reasoning` parameter once instructed and once the schema requires it | Determines whether AC10 holds in practice, and whether R1–R6 compliance is even measurable via the trace | If compliance is low, `VALIDATION_ERROR` rate rises, consuming iteration budget; may force a move to Sonnet for this reason specifically, not just tool-selection quality | Flagged for Validation — check empirically in Phase 4 |
| A2 | R1/R3/R4/R6 (judgement-dependent rules) are followed well enough by Haiku without needing few-shot examples in the system prompt | Keeps the system prompt short (token-cost discipline, `atx-agent-mapping.md`'s context-engineering principles) | If Haiku's rule-following is weak, may need to add 1-2 worked examples to the system prompt, or move to Sonnet | Flagged for Validation — check empirically in Phase 4 |
| A3 | The backend-side dedup safety net (R2/R5) is a nice-to-have, not required for correctness | Keeps Phase 2 scope realistic within the ~4h box | If Haiku violates R2/R5 often in testing, the safety net moves from "if time allows" to "required" | Known — accepted as a Phase 2 stretch item, not a blocker |

## 7. Checklist (self-check against `production-spec-checklist.md`)

- [x] Every rule has a testable acceptance criterion, not a vague "should"
- [x] Delegation boundaries stated explicitly (single bucket, with why)
- [x] What's server-enforceable vs. instruction-only is distinguished, not blurred
- [x] Validation design: 1 happy path, 5 edge cases, 3 failure modes (tool-selection scope)
- [x] Assumptions register: all 3 entries have a status and a validation method
- [x] No contradiction with hard constraint #2 (verified explicitly in §4)
