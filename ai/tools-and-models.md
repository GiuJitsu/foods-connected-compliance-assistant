# Tools & Models Used

Required by the brief's deliverable #2: *"a brief note on which tools and models you worked with."*

## Building the project (AI-assisted development)

- **Claude Code** (Sonnet 5, model id `claude-sonnet-5`) — directed the entire build: spec writing,
  code generation, file/decision tracking. All prompts logged verbatim in `ai/prompts.md`.
- **Playwright MCP** — used by Claude Code as a dev-tool once the frontend exists, to drive the
  browser and verify it against the acceptance criteria in `CLAUDE.md` §"UI interaction design &
  acceptance criteria." Never part of the product agent's own tool catalog. Full rationale:
  `ai/DECISIONS.md` §9.

## Running the product (the app itself)

- **Anthropic API** (user-supplied key) — powers the product agent's reasoning and tool-selection
  loop. Model tier: starting with **Claude Haiku (`claude-haiku-4-5-20251001`, locked P29)**,
  extended thinking enabled (see `CLAUDE.md`
  `specs/agent-spec.md` §10 and `CLAUDE.md` §"Tech stack" for the cost/latency trade-off); may move to Sonnet if
  Haiku's tool-selection reasoning or latency proves inadequate during Phase 2 testing — whichever
  model is actually used ships shown live in the UI's info panel and every task's basis line
  (§"Frontend transparency requirements"), so this is never left ambiguous to an end user.
- **Custom MCP server** (`mcp-server/`, built by us, Python `mcp` SDK) — the only tool source the
  product agent is given, per the brief's MCP-only constraint. Five read-only tools over the mock
  dataset in `mockdata/`. Full contracts: `specs/mcp-integration-spec.md`.
- No mock model adapter is used — a real Anthropic API key is available and used throughout
  (`ai/DECISIONS.md` §4).

## Framework/library choices (not models, listed for completeness)

FastAPI (backend), React + TypeScript + Vite (frontend), pytest (tests). Full rationale for each:
`CLAUDE.md` §"Tech stack."
