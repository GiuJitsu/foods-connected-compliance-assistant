import { expect, test, type Page } from "@playwright/test";
import type { AgentInfo, TaskTrace } from "../src/types";

/**
 * Phase 5 (ai/ROADMAP.md) closed-loop gap-diagnosis pass: e2e.spec.ts only
 * ever exercises whatever state a real task happens to land in — it can't
 * reliably force the 3 FAILED sub-reasons, a limit-hit, or a real
 * hallucination on demand. Those were left honestly marked DOING in
 * ai/ASSESSMENT-CRITERIA.md (F2/F5/F6/F9) rather than overclaimed as DONE.
 * This file closes that gap: mock the network layer with a crafted
 * TaskTrace matching the exact backend/schemas.py shape, and verify the
 * UI renders each state correctly. This tests "does the UI faithfully
 * render this state," not "does the backend ever produce it" — that half
 * is already covered separately by backend/tests/test_agent_loop_failures.py,
 * test_loop_bounds.py, and test_grounding.py.
 */

const INFO: AgentInfo = {
  model: "claude-haiku-4-5-20251001",
  tools: [
    { name: "search_suppliers", description: "" },
    { name: "get_supplier_profile", description: "" },
    { name: "search_specifications", description: "" },
    { name: "search_quality_incidents", description: "" },
    { name: "check_allergen_conflicts", description: "" },
  ],
  iteration_cap: 8,
  per_call_timeout_s: 10,
  total_timeout_s: 60,
};

function baseTrace(overrides: Partial<TaskTrace>): TaskTrace {
  return {
    task_id: "mock-task-1",
    task_input: "mock question",
    status: "COMPLETED",
    limit_hit: "NONE",
    tool_calls: [],
    final_answer: "mock answer",
    failure_reason: null,
    model: INFO.model,
    total_duration_ms: 1200,
    grounding_check: { status: "PASSED", unrecognized_references: [] },
    ...overrides,
  };
}

async function mockBackend(page: Page, finalTrace: TaskTrace) {
  await page.route("**/api/info", (route) => route.fulfill({ json: INFO }));
  await page.route("**/api/tasks", async (route) => {
    if (route.request().method() === "POST") {
      await route.fulfill({ json: { task_id: finalTrace.task_id, status: "IN_PROGRESS" } });
    } else {
      await route.continue();
    }
  });
  await page.route(`**/api/tasks/${finalTrace.task_id}`, (route) => route.fulfill({ json: finalTrace }));
}

async function submit(page: Page) {
  await page.goto("/");
  await page.getByLabel("Ask a compliance question").fill("mock question");
  await page.getByRole("button", { name: "Ask" }).click();
}

test.describe("Compliance Assistant — mocked terminal states", () => {
  test("FAILED / tools unavailable renders distinct, named copy (AC7)", async ({ page }) => {
    await mockBackend(
      page,
      baseTrace({
        status: "FAILED",
        final_answer: null,
        failure_reason: "MCP_UNREACHABLE",
        grounding_check: null,
      }),
    );
    await submit(page);
    await expect(page.locator(".status-title")).toHaveText("Failed — tools unavailable");
    await expect(page.locator(".answer-tag")).toHaveText("Tools unavailable");
    await expect(page.getByText(/MCP server could not be reached/)).toBeVisible();
  });

  test("FAILED / model error renders distinct copy from tools-unavailable (AC8)", async ({ page }) => {
    await mockBackend(
      page,
      baseTrace({
        status: "FAILED",
        final_answer: null,
        failure_reason: "MODEL_API_FAILURE",
        grounding_check: null,
      }),
    );
    await submit(page);
    await expect(page.locator(".status-title")).toHaveText("Failed — model error");
    await expect(page.locator(".answer-tag")).toHaveText("Model error");
  });

  test("FAILED / internal error renders its own distinct copy (3rd failure_reason bucket)", async ({ page }) => {
    await mockBackend(
      page,
      baseTrace({
        status: "FAILED",
        final_answer: null,
        failure_reason: "INTERNAL_ERROR",
        grounding_check: null,
      }),
    );
    await submit(page);
    await expect(page.locator(".status-title")).toHaveText("Failed — internal error");
    await expect(page.locator(".answer-tag")).toHaveText("Internal error");
  });

  test("COMPLETED_PARTIAL / iteration cap names the limit explicitly (AC6)", async ({ page }) => {
    await mockBackend(page, baseTrace({ status: "COMPLETED_PARTIAL", limit_hit: "ITERATION_CAP" }));
    await submit(page);
    await expect(page.locator(".status-title")).toHaveText("Completed — partial");
    await expect(page.locator(".status-sub")).toContainText("iteration cap");
    await expect(page.getByText(/call limit reached/)).toBeVisible();
  });

  test("COMPLETED_PARTIAL / total timeout names the limit explicitly (AC6)", async ({ page }) => {
    await mockBackend(page, baseTrace({ status: "COMPLETED_PARTIAL", limit_hit: "TIMEOUT" }));
    await submit(page);
    await expect(page.locator(".status-sub")).toContainText("total timeout");
    await expect(page.getByText(/time limit reached/)).toBeVisible();
  });

  test("COMPLETED_PARTIAL / a failed call with no limit hit blames the call, not a limit", async ({ page }) => {
    await mockBackend(page, baseTrace({ status: "COMPLETED_PARTIAL", limit_hit: "NONE" }));
    await submit(page);
    await expect(page.locator(".status-sub")).toContainText("a tool call failed");
    await expect(page.locator(".answer-tag")).toHaveText("Partial — a tool call failed");
  });

  test("grounding FLAGGED warning shown on an otherwise-COMPLETED answer (AC15)", async ({ page }) => {
    await mockBackend(
      page,
      baseTrace({
        status: "COMPLETED",
        final_answer: "Supplier SUP-099 is fully compliant.",
        grounding_check: { status: "FLAGGED", unrecognized_references: ["SUP-099"] },
      }),
    );
    await submit(page);
    await expect(page.locator(".status-title")).toHaveText("Completed");
    await expect(page.locator(".grounding-note.flagged")).toBeVisible();
    await expect(page.locator(".grounding-note.flagged")).toContainText("SUP-099");
  });

  test("all 4 tool-error categories render as visually distinct chips in one trace (AC4)", async ({ page }) => {
    const now = new Date().toISOString();
    await mockBackend(
      page,
      baseTrace({
        status: "COMPLETED_PARTIAL",
        tool_calls: [
          {
            timestamp: now,
            tool_name: "search_suppliers",
            input: { category: "CHEESE" },
            reasoning: "r1",
            thinking: null,
            result_summary: "",
            success: false,
            error: { type: "VALIDATION_ERROR", message: "category must be one of DAIRY, PRODUCE, MEAT, BAKERY, SEAFOOD" },
            latency_ms: 5,
          },
          {
            timestamp: now,
            tool_name: "get_supplier_profile",
            input: { supplier_id: "SUP-999" },
            reasoning: "r2",
            thinking: null,
            result_summary: "",
            success: false,
            error: { type: "NOT_FOUND", message: "Supplier SUP-999 not found" },
            latency_ms: 5,
          },
          {
            timestamp: now,
            tool_name: "get_supplier_profile",
            input: { supplier_id: "SUP-TIMEOUT-01" },
            reasoning: "r3",
            thinking: null,
            result_summary: "",
            success: false,
            error: { type: "TIMEOUT", message: "tool call exceeded 10s" },
            latency_ms: 10000,
          },
          {
            timestamp: now,
            tool_name: "search_specifications",
            input: {},
            reasoning: "r4",
            thinking: null,
            result_summary: "",
            success: false,
            error: { type: "SERVER_ERROR", message: "unexpected internal fault" },
            latency_ms: 5,
          },
        ],
      }),
    );
    await submit(page);
    await expect(page.locator(".status-chip.validation")).toBeVisible();
    await expect(page.locator(".status-chip.notfound")).toBeVisible();
    await expect(page.locator(".status-chip.timeout")).toBeVisible();
    await expect(page.locator(".status-chip.server")).toBeVisible();
    await page.screenshot({ path: "test-results/screenshots/05-error-categories.png", fullPage: true });
  });

  test("the question field clears itself after submitting, ready for the next question", async ({ page }) => {
    await mockBackend(page, baseTrace({ status: "COMPLETED" }));
    await page.goto("/");
    const input = page.getByLabel("Ask a compliance question");
    await input.fill("mock question");
    await page.getByRole("button", { name: "Ask" }).click();
    await expect(input).toHaveValue("");
  });
});
