import type { TaskTrace } from "../types";

type Tone = "progress" | "complete" | "partial" | "failed";

function describe(trace: TaskTrace): { label: string; tone: Tone; sub: string } {
  const seconds = (trace.total_duration_ms / 1000).toFixed(2);

  if (trace.status === "IN_PROGRESS") {
    return { label: "In progress", tone: "progress", sub: "waiting on the agent…" };
  }

  if (trace.status === "COMPLETED") {
    return {
      label: "Completed",
      tone: "complete",
      sub: `${trace.tool_calls.length} tool call(s) · ${seconds}s`,
    };
  }

  if (trace.status === "COMPLETED_PARTIAL") {
    const reason =
      trace.limit_hit !== "NONE"
        ? `limit hit: ${trace.limit_hit === "ITERATION_CAP" ? "iteration cap" : "total timeout"}`
        : "a tool call failed";
    return {
      label: "Completed — partial",
      tone: "partial",
      sub: `${reason} · ${trace.tool_calls.length} call(s) · ${seconds}s`,
    };
  }

  // FAILED — AC7 / AC8, plus INTERNAL_ERROR (build-loop-fix-log gap #3)
  const reasonLabel =
    trace.failure_reason === "MCP_UNREACHABLE"
      ? "tools unavailable"
      : trace.failure_reason === "MODEL_API_FAILURE"
        ? "model error"
        : "internal error";
  return { label: `Failed — ${reasonLabel}`, tone: "failed", sub: `${seconds}s before failing` };
}

/** ZONE 3: status banner — 4 visually distinct states (AC5, AC6, AC7, AC8). */
export function StatusBanner({ trace }: { trace: TaskTrace }) {
  const { label, tone, sub } = describe(trace);
  return (
    <div className={`status-banner tone-${tone}`}>
      <span className="status-dot" />
      <span className="status-title">{label}</span>
      <span className="status-sub">{sub}</span>
    </div>
  );
}
