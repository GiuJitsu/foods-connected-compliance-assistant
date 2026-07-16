import type { FailureReason, TaskTrace } from "../types";

/** The 3 distinct FAILED sub-reasons (specs/agent-spec.md §9): MCP
 * unreachable at task start, model/API failure mid-task, and an unexpected
 * internal fault (ai/build-loop-fix-log.md gap #3). Never shows a raw
 * exception — the backend never sends one (hard constraint #5). */
const COPY: Record<FailureReason, { title: string; body: string }> = {
  MCP_UNREACHABLE: {
    title: "Tools unavailable",
    body: "The MCP server could not be reached at the start of this task, so no tools were ever called. This is a clean stop, not a partial answer.",
  },
  MODEL_API_FAILURE: {
    title: "Model error",
    body: "The underlying model/API failed mid-task. Any tool calls made before the failure are shown above.",
  },
  INTERNAL_ERROR: {
    title: "Internal error",
    body: "Something went wrong inside the agent itself — not the model and not the tools. Any tool calls made before the failure are shown above.",
  },
};

export function FailureCard({ trace }: { trace: TaskTrace }) {
  const info = (trace.failure_reason && COPY[trace.failure_reason]) || {
    title: "Failed",
    body: "The task did not complete.",
  };

  return (
    <div className="answer-card">
      <span className="answer-tag critical">{info.title}</span>
      <p className="answer-text">{info.body}</p>
      <details className="raw-json-toggle">
        <summary>View raw trace JSON</summary>
        <pre className="json">{JSON.stringify(trace, null, 2)}</pre>
      </details>
    </div>
  );
}
