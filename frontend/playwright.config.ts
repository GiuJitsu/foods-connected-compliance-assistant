import { defineConfig, devices } from "@playwright/test";

/**
 * Dev-only tool (CLAUDE.md §"Tech stack" — never part of the product agent's
 * own tool catalog). Assumes both servers are already running:
 *   backend:  http://localhost:8000  (python -m uvicorn main:app --port 8000)
 *   frontend: http://localhost:5173  (npm run dev)
 * Not auto-started here since the backend needs a real ANTHROPIC_API_KEY and
 * the MCP server subprocess — outside what a `webServer` config can own.
 */
export default defineConfig({
  testDir: "./tests",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost:5173",
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
