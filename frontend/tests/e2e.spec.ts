import { expect, test } from "@playwright/test";

/**
 * Closed-build-loop pass for Phase 3 (CLAUDE.md §"Verification approach"):
 * drive the browser through the acceptance criteria (AC1-AC15) against the
 * real backend + real MCP server. Not exhaustive of every AC — a spot check
 * of the ones only a real browser can confirm (client-side blocking,
 * immediate-in-progress rendering, real DOM structure), since the API
 * contract itself is already covered by backend/tests/.
 */

test.describe("Compliance Assistant", () => {
  test("static info panel loads with the real tool catalog (AC12)", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("claude-haiku-4-5-20251001")).toBeVisible();
    await expect(page.locator(".board-tools li")).toHaveCount(5);
  });

  test("empty submission is blocked client-side, never reaches the backend (AC1)", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "Ask" }).click();
    await expect(page.locator(".field-note")).toHaveText("Type a question before asking.");
    // No trace should ever have started
    await expect(page.locator(".empty-state")).toBeVisible();
  });

  test("a real task runs end-to-end and renders the full trace (AC2, AC3, AC5, AC10, AC11, AC13)", async ({
    page,
  }) => {
    await page.goto("/");
    await page.getByLabel("Ask a compliance question").fill("Is supplier SUP-013 currently compliant?");
    await page.getByRole("button", { name: "Ask" }).click();

    // AC2: shows "in progress" immediately, before any tool call resolves
    await expect(page.locator(".status-title")).toHaveText("In progress");
    await page.screenshot({ path: "test-results/screenshots/01-in-progress.png", fullPage: true });

    // Real Anthropic + real MCP call — poll to a terminal state
    await expect(page.locator(".status-title")).not.toHaveText("In progress", { timeout: 45_000 });

    // AC3/AC10: at least one trace entry with a visible reasoning line
    await expect(page.locator(".trace-entry").first()).toBeVisible();
    await expect(page.locator(".trace-reasoning").first()).not.toBeEmpty();

    // AC11: basis line present
    await expect(page.locator(".basis-line")).toBeVisible();

    // AC13: raw trace JSON is revealable
    await page.getByText("View raw trace JSON").click();
    await expect(page.locator("pre.json")).toBeVisible();
    await expect(page.locator("pre.json")).toContainText('"task_id"');

    await page.screenshot({ path: "test-results/screenshots/02-completed.png", fullPage: true });
  });

  test("dark mode renders with adapted tokens", async ({ page }) => {
    await page.emulateMedia({ colorScheme: "dark" });
    await page.goto("/");
    await expect(page.locator(".sidebar")).toBeVisible();
    await page.screenshot({ path: "test-results/screenshots/03-dark-mode.png", fullPage: true });
  });
});
