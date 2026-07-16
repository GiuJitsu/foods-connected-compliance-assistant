# Test Log

A point-in-time record of full test-suite runs, kept separate from `ai/ASSESSMENT-CRITERIA.md`
(which tracks *what's covered*, not *when it last ran and what it printed*). Updated whenever a
full run is repeated for the record — not a running append-only journal like `ai/prompts.md`;
supersede the relevant section on a re-run rather than stacking duplicates, and note what changed.

---

## Run 1 — 2026-07-16, full suite including real-LLM tests (P34)

**Command / environment:**
- Python 3.12.10, pytest 9.1.1
- `ANTHROPIC_API_KEY` set as a persistent Windows user environment variable (via `setx`, run by
  the user in their own terminal — never pasted into this chat or any file; verified present here
  only by checking the variable's *length*, never its value, per CLAUDE.md hard constraint #3)
- `cd mcp-server && python -m pytest -v`
- `cd backend && python -m pytest -v`

### mcp-server/ — 10/10 passed (0.78s)

Direct-call unit tests against the real `mockdata/`, covering every edge case in
`CLAUDE.md` §"Testing scenarios & required mock data" (E1–E6), closing
`ai/ASSESSMENT-CRITERIA.md` row T4 — previously only manually verified in Phase 1.

| Test | Covers |
|---|---|
| `test_e1_empty_result_set_is_not_an_error` | E1 — legitimate zero-row filter (`since_date=2099-01-01`) |
| `test_e2_supplier_with_zero_certifications_is_a_valid_profile` | E2 — SUP-017, empty `certifications: []`, not an error |
| `test_e3_invalid_enum_value_is_an_explicit_validation_error` | E3 — `category="CHEESE"` → `VALIDATION_ERROR` |
| `test_e3_blank_reasoning_is_an_explicit_validation_error` | structural `reasoning` enforcement, blank string |
| `test_e4_embedded_instruction_text_is_returned_verbatim_not_sanitized` | E4 — INC-003's injection text round-trips unchanged |
| `test_e5_allergen_conflict_empty_allergens_never_conflicts` | E5 — SPEC-008, empty allergens |
| `test_e5_allergen_conflict_multiple_allergens_flags_every_match` | E5 — SPEC-019, 3 allergens, 2-way match |
| `test_e6_certification_expiring_on_the_reference_date_is_returned_as_expired` | E6 — CERT-020, `expiry_date` == dataset's fixed "today" (2026-07-16) |
| `test_unknown_supplier_id_is_not_found_not_fabricated` | `get_supplier_profile` NOT_FOUND contract |
| `test_unknown_specification_id_is_not_found_never_a_false_negative` | `check_allergen_conflicts` NOT_FOUND contract |

### backend/ — 23/23 passed, 40.04s (1 unrelated deprecation warning: `httpx`/`starlette.testclient`)

| File | Tests | What it proves |
|---|---|---|
| `test_agent_loop_failures.py` | 3 | The 3 required failure scenarios (MCP unreachable, tool error mid-task, model/API failure) each end in a clean, meaningful state |
| `test_agent_loop_happy_path.py` | 1 | Multi-target tool chaining, fake model + fake MCP |
| `test_api.py` | 5 | HTTP contract (status codes, immediate `IN_PROGRESS`, 404, `/api/info` shape) — loop stubbed |
| `test_dedup.py` | 1 | R2/R5 identical-call safety net served from cache |
| `test_end_to_end_http.py` | 1 | **New (P31/P34).** True end-to-end: real HTTP POST → real background `run_task()` (not stubbed) → real MCP server subprocess → poll to `COMPLETED` over the actual API a frontend would call |
| `test_grounding.py` | 4 | Anti-hallucination mechanical backstop (`compute_grounding_check`), including a model-invents-an-ID end-to-end case |
| `test_loop_bounds.py` | 2 | Iteration cap and total-timeout enforcement, no hang |
| `test_real_llm_integration.py` | 3 | **New (P34), real Anthropic API spend.** See below |
| `test_real_mcp_integration.py` | 3 | Fake model + the real MCP server over real stdio protocol |

### Real-LLM tests, in detail (`test_real_llm_integration.py`) — the one combination no other test covers: real Anthropic model + real MCP server, both genuinely live

1. **`test_real_model_answers_a_zero_certifications_lookup_honestly`** — asked the real model
   whether SUP-017 has any certifications. It cannot know this from training data (the dataset is
   fabricated for this project); it called a real tool on its own decision (hard constraint #2,
   nothing scripted), got the real empty-`certifications` result, and reported it honestly.
   `reasoning` was present and non-blank on the real call, same as the structural requirement
   enforces for fake-model tests.
2. **`test_real_model_reports_a_legitimate_empty_result_without_fabricating`** — asked about
   incidents "since the year 2099." The model called a real tool, got a genuine zero-row result,
   and the grounding mechanical backstop confirmed `PASSED` — no invented ID appeared in the
   answer.
3. **`test_real_model_never_leaks_a_raw_exception_on_a_real_run`** — a general real-run sanity
   check: never ends in `FAILED`/`INTERNAL_ERROR` (hard constraint #5).

All three passed on the first real run — no retries needed, no gap found. This is the first time in
the project a real Anthropic API key has been exercised end-to-end; the model actually chosen
(`claude-haiku-4-5-20251001`, `CLAUDE.md` §"Tech stack") is strong enough at tool selection and
grounded answering for this dataset's scope, so the earlier open question in `ai/DECISIONS.md`
§"Open questions" (Haiku vs. Sonnet, "confirm during build if tool-selection reasoning is strong
enough") is resolved: **Haiku is sufficient, no move to Sonnet needed.**

**Cost/repeatability note:** this test file is marked `pytest.mark.skipif` on the absence of
`ANTHROPIC_API_KEY`, so a routine `pytest` run (CI, or any machine without the key configured)
skips it automatically and spends nothing — this run was a deliberate, manual invocation with the
key present, not something that runs by default. Full reasoning: `ai/DECISIONS.md` §31/§32.

### Grand total: **33/33 tests passed**, 0 failures, 3 auto-skipped only when no key is present.

Evidence pointer updated in `ai/ASSESSMENT-CRITERIA.md` rows T1, T4, M1; `ai/ROADMAP.md` Phase 4
marked DONE.
