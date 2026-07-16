# MCP Integration Spec: Foods Connected Compliance Assistant — Custom MCP Server

Written against the shape of `AI FDE Training/Reference/integration-spec-template.md`, adapted from
a REST-integration template to an MCP tool-server integration. This is the spec the MCP server
(`mcp-server/`) and its mock dataset (`mockdata/`) are built from — update this file first if a
contract changes, then update the code. Compact contract table (for quick reference during the
build) stays in `CLAUDE.md` §"MCP tool contracts"; this file is the full version.

---

## 1. Integration Purpose

**What:** A locally-run MCP server exposing five read-only tools over a mock food-supply-chain
compliance dataset (suppliers, certifications, specifications, quality incidents). The backend
agent loop connects to it as an MCP client and lets the model choose which tools to call.

**Why:** This is the assessment's core requirement — tools must be consumed over MCP, and the model
must choose among them inside a bounded loop, not follow a hardcoded sequence.

**Responsibility:** The MCP server is responsible for: validating tool input against each tool's
schema; querying the mock dataset; returning results (or an explicit error) in the documented
shape; and never crashing the backend process on bad input or an internal fault (see §9).

**What the MCP server is NOT responsible for:** deciding which tools to call (that's the model,
in the agent loop); interpreting or synthesising an answer (that's the model); any write/mutation
to the dataset (all five tools are read-only); authenticating the end user (out of scope — this is
a local demo server, not a multi-tenant service).

---

## 2. System Description

**System name:** `foods-connected-compliance-mcp` (working name for the server process)

**Transport:** stdio, per the MCP Python SDK's standard local-server pattern — the backend spawns
the server as a subprocess and communicates over stdin/stdout. No network exposure; nothing to
firewall or authenticate for a local demo.

**Data source:** static, in-memory dataset loaded once at server startup from `mockdata/` (JSON
files — see `mockdata/NOTES.md` once created, not `mockdata/README.md`, per the naming-collision
lesson in `ai/DECISIONS.md` §18 — confirm with the user before creating it, per the P14
file-creation rule). No live external system behind it.

**Supported operations (tools):** `search_suppliers`, `get_supplier_profile`,
`search_specifications`, `search_quality_incidents`, `check_allergen_conflicts`. Full contracts in
§4.

**Uptime / backup plan:** N/A — this is a local subprocess started and owned by the backend, not an
external SLA'd service. If the subprocess fails to start or dies mid-task, that's handled as an
"MCP server unreachable" failure mode (§9), not a backup-endpoint failover.

---

## 3. Authentication & Authorization

**Method:** none. This is a local, single-process, mock-data server with no real client data behind
it — there's nothing to protect. Explicitly stated here (rather than left unspecified) so it's a
documented decision, not an oversight, per the production-spec-checklist discipline of never
leaving an integration's auth section implicit.

---

## 4. Tool Contracts

All five tools are read-only. Each is specified as: purpose, input schema, output schema, worked
example, and error behaviour.

**All five tools require a `reasoning` string parameter** (why this call is being made) —
structural enforcement for the transparency requirement, not just a system-prompt request. See
`specs/agent-spec.md` for the full design rationale. Server-side validation: missing or
empty/whitespace-only `reasoning` → `VALIDATION_ERROR` on that tool, same as any other missing
required field — this is deliberately a hard failure, not a soft warning, since a silently-accepted
empty reasoning would defeat the whole point of making it required.

### `search_suppliers`

**Purpose:** find suppliers matching optional filters.

**Input:**
```json
{
  "query": "string, optional — case-insensitive substring match on Supplier.name",
  "category": "enum [DAIRY, PRODUCE, MEAT, BAKERY, SEAFOOD], optional",
  "country": "string, optional — ISO 3166-1 alpha-2 code",
  "risk_rating": "enum [LOW, MEDIUM, HIGH], optional",
  "reasoning": "string, required — brief statement of why this call is being made (see §agent-spec's structural-enforcement design; schema-required on all 5 tools, not just this one)"
}
```

**Output:**
```json
{
  "results": [
    {"id": "string", "name": "string", "country": "string", "category": "enum", "risk_rating": "enum"}
  ],
  "count": "integer"
}
```
Max 20 results.

**Example:** `{"category": "DAIRY", "country": "IT"}` → suppliers in Italy, dairy category.

**Error behaviour:** no matches → `{"results": [], "count": 0}` (not an error — a real answer).
Invalid enum value (e.g. `category: "CHEESE"`) → explicit tool error
`{"error": "INVALID_FILTER_VALUE", "field": "category", "message": "..."}`; the server does not
silently ignore the bad filter and return unfiltered results.

### `get_supplier_profile`

**Purpose:** full profile for one supplier — its details plus all its certifications.

**Input:** `{"supplier_id": "string, required", "reasoning": "string, required — see search_suppliers note above"}`

**Output:**
```json
{
  "supplier": {"id": "...", "name": "...", "country": "...", "category": "...", "risk_rating": "..."},
  "certifications": [
    {"id": "...", "standard": "enum", "status": "enum", "expiry_date": "ISO 8601 date"}
  ]
}
```

**Error behaviour:** unknown `supplier_id` → `{"error": "SUPPLIER_NOT_FOUND", "supplier_id": "..."}`
— never a fabricated or empty-but-200-shaped record. **Reserved test ID `SUP-TIMEOUT-01`**
deliberately raises a simulated timeout (server sleeps past the client's 10s per-call timeout) to
exercise mid-task tool-error handling in tests without depending on a real network fault.

### `search_specifications`

**Purpose:** find product specifications matching optional filters.

**Input:**
```json
{
  "query": "string, optional — substring match on Specification.name",
  "supplier_id": "string, optional",
  "category": "enum [DAIRY, PRODUCE, MEAT, BAKERY, SEAFOOD], optional",
  "reasoning": "string, required — see search_suppliers note above"
}
```

**Output:**
```json
{
  "results": [
    {"id": "...", "supplier_id": "...", "name": "...", "category": "enum", "allergens": ["enum", "..."], "status": "enum"}
  ],
  "count": "integer"
}
```

**Error behaviour:** no matches, including an unknown `supplier_id` used as a filter → empty list
(this is a filter, not a lookup by primary key — an unknown filter value legitimately produces zero
rows, that's not an error condition).

### `search_quality_incidents`

**Purpose:** find quality incidents (recalls, complaints, non-conformances) matching optional
filters.

**Input:**
```json
{
  "specification_id": "string, optional",
  "supplier_id": "string, optional",
  "since_date": "ISO 8601 date, optional",
  "type": "enum [RECALL, COMPLAINT, NON_CONFORMANCE], optional",
  "reasoning": "string, required — see search_suppliers note above"
}
```

**Output:**
```json
{
  "results": [
    {"id": "...", "specification_id": "...", "date": "ISO 8601 date", "type": "enum", "severity": "enum", "description": "string"}
  ],
  "count": "integer"
}
```

**Error behaviour:** no matches → empty list. This tool is the one guaranteed, by dataset design,
to return an empty list for at least one realistic filter combination (§ mockdata design, edge
case E1) — used to verify the agent reports "no incidents found" rather than inventing one.

### `check_allergen_conflicts`

**Purpose:** check whether a specification's allergens overlap with a caller-supplied avoid-list.

**Input:**
```json
{
  "specification_id": "string, required",
  "allergens_to_avoid": "array of enum [MILK, EGGS, GLUTEN, PEANUTS, TREE_NUTS, SOY, FISH, SHELLFISH, SESAME], required, non-empty",
  "reasoning": "string, required — see search_suppliers note above"
}
```

**Output:**
```json
{
  "specification_id": "...",
  "conflicts": ["enum", "..."],
  "has_conflict": "boolean"
}
```

**Error behaviour:** unknown `specification_id` → `{"error": "SPECIFICATION_NOT_FOUND", ...}` —
never a false `has_conflict: false`, which would look like a real (and wrong) safety answer.
Empty `allergens_to_avoid` → `{"error": "INVALID_INPUT", "message": "allergens_to_avoid must be non-empty"}`.

---

## 5. Error Handling & Retry Logic

| Condition | Server response | Agent-loop retry policy |
|---|---|---|
| Valid input, no matching rows | Success response, empty `results`/`count: 0` | N/A — not an error |
| Invalid enum / malformed input | Tool error result, specific error code | No retry — this will fail identically every time; agent should adjust its input or give up on that path |
| Unknown ID on a lookup tool (`get_supplier_profile`, `check_allergen_conflicts`) | Explicit `*_NOT_FOUND` error | No retry — same reasoning |
| Simulated timeout (`SUP-TIMEOUT-01` only) | No response within 10s | Backend agent loop treats as a tool-call timeout: log the failure, continue the loop with remaining budget, do not retry the same call automatically (retrying a deterministic timeout wastes iteration budget) |
| MCP server process unreachable/crashed | Connection error at the transport level, not a tool-level error | Backend fails the task immediately at loop start with a clear "tools unavailable" state — does not attempt the loop at all (see CLAUDE.md §"Escalation / failure behaviour" #1) |

---

## 6. Rate Limits & Throttling

N/A. Local in-process mock server, single backend client, no external consumers. Documented
explicitly rather than left unspecified.

---

## 7. Data Mapping

The MCP server's tool responses map 1:1 onto the `mockdata/` JSON records — we control both sides,
so there's no external-system field-name translation to document. The one non-trivial mapping is
`Certification.status` derivation for any "is this supplier currently compliant" style question:
`VALID` = compliant, `EXPIRED`/`SUSPENDED` = not — the tool returns the raw `status` value and
leaves that interpretation to the model, it does not pre-compute a boolean "is_compliant" field
(keeps the tool a pure data source, keeps the reasoning with the model per hard constraint #2).

---

## 8. State Synchronization

Mock dataset is loaded once at server startup and held in memory for the process lifetime. No live
sync, no write path, no cache invalidation to design — explicitly out of scope, since there is no
upstream system to sync from.

---

## 9. Failure Modes & Fallbacks

| Failure mode | Trigger | Handling |
|---|---|---|
| MCP server unreachable | Subprocess fails to start, or dies mid-task | Backend surfaces a clear "tools unavailable" error before attempting the loop (task start) or as an immediate task failure (mid-task); frontend shows this as a distinct failure state, not a generic error |
| Tool call error mid-task | Any tool returns an error result (bad input, not-found, simulated timeout) | Logged to the tool-call trace with the error; agent continues within remaining iteration budget if an alternative path exists, otherwise reports the partial answer + what failed |
| Malformed tool call from the model | Model calls a tool with input that fails schema validation | Server returns a structured validation error (not a crash); this is logged in the trace like any other tool error |

---

## 10. Monitoring & Logging

Every tool call, successful or not, is logged by the backend (not the MCP server itself) into the
task's trace object — this is the same trace the frontend renders for transparency. Two levels:
per-call entries, and one task-level summary.

**Per-call entry** (one per tool call, in order):
```json
{
  "timestamp": "ISO 8601",
  "tool_name": "string",
  "input": { "...": "as sent to the tool" },
  "reasoning": "string — the tool call's own required `reasoning` input parameter (§4), copied verbatim into the trace; not parsed from preceding assistant text and not fabricated after the fact",
  "thinking": "string, nullable — raw extended-thinking content for this step, when the model produced one; shown in the UI collapsed by default with an explicit non-authoritative caption (CLAUDE.md §'On chain-of-thought')",
  "result_summary": "string — short human-readable summary, not the full raw payload",
  "success": "boolean",
  "error": {
    "type": "enum [VALIDATION_ERROR, NOT_FOUND, TIMEOUT, SERVER_ERROR], present only if success == false",
    "message": "string, present only if success == false"
  },
  "latency_ms": "integer"
}
```
`error.type` maps directly onto the per-tool error behaviours in §4: `VALIDATION_ERROR` (invalid
enum/malformed input), `NOT_FOUND` (unknown ID on a lookup tool), `TIMEOUT` (the reserved
`SUP-TIMEOUT-01` fixture), `SERVER_ERROR` (anything unexpected). This is what lets the frontend
show *why* a call failed, not just that it failed (CLAUDE.md §"Frontend transparency requirements").
`reasoning` is deliberately a short, explicit, schema-required rationale — not raw hidden
chain-of-thought, which is surfaced separately via `thinking` and is not appropriate to conflate
with this field (`CLAUDE.md` §"On chain-of-thought").

**Task-level summary** (one per task, wraps the ordered list of per-call entries):
```json
{
  "task_input": "string — the user's original submission",
  "status": "enum [IN_PROGRESS, COMPLETED, COMPLETED_PARTIAL, FAILED]",
  "limit_hit": "enum [NONE, ITERATION_CAP, TIMEOUT] — explicit, not inferred by the frontend",
  "tool_calls": "[ ...per-call entries, ordered ]",
  "final_answer": "string, present unless status == FAILED",
  "failure_reason": "enum [MCP_UNREACHABLE, MODEL_API_FAILURE], present only if status == FAILED",
  "model": "string — which model produced this answer, e.g. 'claude-haiku-4-5' (§'Tech stack' in CLAUDE.md for the actual model id in use)",
  "total_duration_ms": "integer — whole-task wall-clock time, for the final answer's basis line"
}
```
The frontend's "basis line" (CLAUDE.md §"Frontend transparency requirements" #5) — call
success/fail counts, model, total time — is derived client-side from `tool_calls` + `model` +
`total_duration_ms`; no separate duplicated field needed for it.

**`COMPLETED_PARTIAL` semantics, clarified (Integrity Check #1, finding 8):** this status fires
whenever the final answer doesn't fully resolve the task, for either of two independent causes,
both of which must set `status = COMPLETED_PARTIAL` — `limit_hit` just distinguishes which:
1. The iteration cap or total timeout was reached → `limit_hit = ITERATION_CAP` or `TIMEOUT`.
2. A tool call failed mid-task with no alternative path, but the loop otherwise concluded within
   its budget → `limit_hit = NONE`; the reason is visible via the failed entry/entries in
   `tool_calls`. A plain `COMPLETED` status must never be used when the answer is actually
   incomplete for this reason.

This log entry shape is the direct input to the frontend's tool-activity timeline and status
display (see `CLAUDE.md` §"Frontend transparency requirements", brief requirements F2–F7 and A4 in
`ai/ASSESSMENT-CRITERIA.md`). `limit_hit` and `status` are deliberately explicit fields, not left
for the frontend to infer from the tool-call list — the brief's transparency bar is "why the answer
is what it is," which requires the *reason* to be a first-class signal, not a derived guess.

---

## 11. Additional Constraints & Notes

- **No real data.** Every record in `mockdata/` is fabricated. No real Foods Connected supplier,
  client, or product data is used anywhere in this project.
- **Versioning:** N/A — single local server, no external consumers to version against.
- **Security note:** one quality incident's `description` field deliberately contains embedded
  instruction-like text (see CLAUDE.md §"Testing scenarios & required mock data" E4) — this is
  intentional test data proving the agent treats tool output as data, not instructions. It is not a
  real vulnerability in the server; the server returns it verbatim like any other field, exactly as
  a real external system's untrusted content would arrive.

---

## 12. Checklist

- [x] Integration purpose is clear
- [x] System description (local stdio server, static mock data source)
- [x] Authentication explicit (none, and why)
- [x] All five tools fully specified: input, output, example, error behaviour
- [x] Error handling defined per condition, with retry policy
- [x] Rate limits explicit (N/A, and why)
- [x] Data mapping documented (trivial here, and why — stated explicitly rather than assumed)
- [x] State synchronization approach stated (static, load-once)
- [x] Failure modes have explicit handling
- [x] Monitoring/logging shape defined, tied directly to the frontend transparency requirement
- [x] Mock-data-only disclaimer included
