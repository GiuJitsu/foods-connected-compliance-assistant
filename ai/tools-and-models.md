# Tools & Models Used

Required by the brief's deliverable #2: *"a brief note on which tools and models you worked with."*
Expanded (P42) beyond the original two-model summary to cover every tool, protocol, and Claude Code
capability that actually shaped the build — not just the two models — per the user's request to
explain each one clearly: what it does, why it was used, and where the evidence is.

## 1. Models

### Product agent (the app itself)

**Anthropic API, Claude Haiku (`claude-haiku-4-5-20251001`)**, extended thinking enabled. Powers the
agent loop's reasoning and tool-selection decisions (`backend/model_client.py`'s
`AnthropicModelClient`). Chosen per the brief's explicit welcome of small/inexpensive models
(`CLAUDE.md` §"Tech stack"). **Confirmed final, not provisional**: run for real against the live API
in `backend/tests/test_real_llm_integration.py` — correct, unscripted tool selection and honest
empty-result handling on the first real run, full results in `ai/test-log.md` — so the standing
"Haiku vs. Sonnet" question (open since Phase 0) is resolved without needing Sonnet. Extended
thinking is shown to the end user per tool-call step, behind a collapsed disclosure
(`specs/agent-spec.md` §10). Whichever model actually answered a task is always shown live in the
UI's info panel and every task's basis line — never left ambiguous.

### Build agent (directing this repository)

**Claude Code, Sonnet 5** (model id `claude-sonnet-5`) — directed the entire build: spec writing,
code generation, decision-making, and every artefact in `ai/`. Every significant prompt sent to it
is logged verbatim in `ai/prompts.md`; every decision it locked in is logged with reasoning in
`ai/DECISIONS.md`. The two are architecturally distinct and never conflated — see `CLAUDE.md`'s
opening "Two agents, not one."

## 2. MCP (Model Context Protocol)

The protocol the entire product is built around — hard constraint #1 in `CLAUDE.md` ("Tools must be
consumed over MCP. No tool may be wired directly into the backend outside the protocol"). Two roles:

- **`mcp-server/`** — a custom-built MCP server (Python `mcp` SDK, `FastMCP`, stdio transport)
  exposing 5 read-only tools over the mock food-supply-chain dataset. Built instead of using
  GitHub's public MCP server for thematic relevance to Foods Connected and full control over the
  deliberate failure/edge-case scenarios the brief grades (`ai/DECISIONS.md` §5).
- **`backend/mcp_client.py`** — `StdioMCPClient`, the real client the agent loop uses to spawn that
  server as a subprocess and speak the actual MCP wire protocol to it (handshake, `list_tools`,
  `call_tool`). Verified genuinely speaking the real protocol, not just calling Python functions
  directly, in `backend/tests/test_real_mcp_integration.py`.

Both sides are the *same* `mcp` SDK, used for two different roles — this is why hard constraint #1
is actually enforced structurally: `backend/` has no direct Python import of anything in
`mcp-server/`, only a subprocess + stdio connection.

## 3. Claude Code's own capabilities used during the build

These aren't part of the *product* — they're tools Claude Code itself used while building it. Listed
because the user asked for all tools to be explained, not just the ones that ship in the app.

- **Agent (subagent dispatch)** — spawns an isolated Claude instance with no memory of this
  conversation. Used once, deliberately, for Phase 2: rather than build the backend myself, a fresh
  subagent was given only the 5 build-facing spec files and the exact three-part prompt from the
  training methodology (*"first tell me what you can build confidently, second what you need to
  clarify, third build the confident parts"*) — the point being to test the **spec's** clarity
  against a reader with no access to the intent behind it, which testing against my own memory of
  what I meant could never do. Found 5 real spec gaps this way, logged in
  `ai/build-loop-fix-log.md`. Result independently re-verified afterward (full test suite re-run,
  core files read directly), not taken on the subagent's word.
- **Artifact** — publishes a live, styled HTML page. Used for the frontend's visual design, twice,
  *before* any React code existed: a first pass (ledger/audit aesthetic), then a full pivot on
  explicit user feedback (bigger banner, sidebar, a food-specific palette, a non-office display
  font) — approved as a static page before it was expensive to change as real components. Both
  iterations used real mock data (real supplier names, real IDs, the real `SUP-TIMEOUT-01` fixture),
  never placeholder lorem content.
- **Skill → `artifact-design`** — a packaged set of design-quality instructions loaded before
  building either Artifact iteration. What it does: calibrates how much design effort a request
  actually calls for, and pushes toward a considered, subject-specific token system (named colors,
  paired typefaces, a real layout concept) instead of the handful of looks that AI-generated design
  clusters around by default (warm cream + serif + terracotta, purple-to-blue gradients, `rounded-lg`
  everywhere, emoji section markers). Why used: to get a visual identity actually specific to a food
  supply-chain compliance tool, not a generic dashboard template. Concretely shaped both design
  passes — the second, approved one uses a market/ledger-produce palette (tomato/basil/wheat/
  stone/fig-plum/wine) and a rounded display face specifically because the skill's process pushes for
  subject-grounded, non-templated choices before any code is written.
- **ToolSearch** — looks up tool schemas not already loaded into context. Used to check whether a
  Playwright MCP server was actually connected in this session (`CLAUDE.md`'s original plan). It
  wasn't — nothing matched. That result directly caused the pivot documented in §4 below.
- **AskUserQuestion** — used at genuine decision points where guessing would have been assuming
  rather than confirming: how to install Node.js (winget vs. manual), and earlier, how the MCP
  server should be sourced (custom vs. GitHub's public one), the model-provider question, and
  several repo-structure calls. Per the user's own standing instruction ("don't assume — ask").
- **PowerShell (shell execution)** — every `git`, `npm`, `pip`, `pytest`, `python`, `winget`, and
  `playwright` command run during the build. Windows-specific quirks hit and worked around: PATH not
  persisting across separate tool calls (refreshed explicitly each time), and multi-line commit
  messages with embedded quotes breaking `git commit -m` (fixed by always writing the message to a
  scratchpad file first and using `git commit -F`).
- **Read / Write / Edit / Grep / Glob** — the standard file tools, used throughout; not individually
  notable, listed here only for completeness since the user asked for "all tools used."

## 4. Playwright

Dev-only browser-testing tool — **never** part of the product agent's own tool catalog, and never
used to script the interview demo (the demo is presented live/manually). Originally planned to run
as an MCP server (matching the brief's own "MCP server" framing for tools generally); when
`ToolSearch` found none actually connected in this build session, pivoted to installing
**`@playwright/test` directly as an npm package** in `frontend/` instead — same real-Chromium
verification value, no MCP wrapper needed, and it left behind a persisted, reusable test suite
(`frontend/tests/`) rather than a one-off interactive session. Genuinely earned its place: the first
real run caught an actual bug (a React `StrictMode` polling issue that silently stopped the UI from
ever leaving "In progress," invisible to every other test in this project since none of them involve
a browser) — full account `ai/DECISIONS.md` §34.

## 5. Local development environment

Tools installed onto the build machine during this session, none present at the start — each
confirmed with the user first via `AskUserQuestion` before installing:

| Tool | Installed via | Why |
|---|---|---|
| Python 3.12 | `winget` | Run `mcp-server/` and `backend/` |
| git + GitHub CLI (`gh`) | `winget` | Version control + repo creation (`ai/DECISIONS.md` §25) |
| Node.js LTS | `winget` | Build/run `frontend/` |
| `@playwright/test` + Chromium | `npm` | Real-browser testing, §4 above |

## 6. Frameworks/libraries (not models or dev tools — application dependencies)

FastAPI + Pydantic (backend), React + TypeScript + Vite (frontend), pytest + pytest-asyncio
(automated tests), `@playwright/test` (frontend end-to-end tests). Full rationale for each:
`CLAUDE.md` §"Tech stack."
