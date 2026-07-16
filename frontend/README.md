# Compliance Assistant — frontend

React + TypeScript + Vite. Renders the trace/status contract from `backend/` (`CLAUDE.md`
§"Backend API contract") against the acceptance criteria in `CLAUDE.md`
§"UI interaction design & acceptance criteria" (AC1–AC15). Not a standalone deliverable — see the
repo root `README.md` for the full project.

## Run

```
npm install
npm run dev
```

Expects the backend running at `http://localhost:8000` (the FastAPI default from
`backend/main.py`; override with a `VITE_API_BASE_URL` env var if it's running elsewhere).

## Structure

```
src/
  types.ts                    — mirrors backend/schemas.py exactly (the wire contract)
  api.ts                      — fetch client: submitTask / getTask / getInfo
  hooks/useTask.ts             — submit + poll-to-terminal-status
  components/
    Banner.tsx                — big banner + task input (AC1, AC2)
    Sidebar.tsx                — static info panel, live from GET /api/info (AC12)
    StatusBanner.tsx           — the 4 status states (AC5–AC8)
    TraceList.tsx               — ordered tool-call trace (AC3, AC4, AC10, AC14)
    AnswerCard.tsx              — basis line, grounding warning, raw JSON (AC11, AC13, AC15)
    FailureCard.tsx             — the 3 distinct FAILED sub-reasons
```
