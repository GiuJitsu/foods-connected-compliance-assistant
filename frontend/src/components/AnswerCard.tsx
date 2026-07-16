import type { TaskTrace } from "../types";

/** ZONE 5 (success/partial path): final answer, basis line (AC11), raw
 * trace JSON (AC13), and the grounding warning (AC15) shown for both
 * COMPLETED and COMPLETED_PARTIAL — grounding_check is only ever computed
 * on this path, never on a FAILED trace (backend/agent_loop.py). */
export function AnswerCard({ trace }: { trace: TaskTrace }) {
  const succeeded = trace.tool_calls.filter((c) => c.success).length;
  const failed = trace.tool_calls.length - succeeded;
  const isPartial = trace.status === "COMPLETED_PARTIAL";

  return (
    <div className="answer-card">
      {isPartial && (
        <span className="answer-tag">
          Partial —{" "}
          {trace.limit_hit !== "NONE"
            ? `${trace.limit_hit === "ITERATION_CAP" ? "call limit" : "time limit"} reached`
            : "a tool call failed"}
        </span>
      )}

      <p className="answer-text">{trace.final_answer}</p>

      <div className="basis-line">
        <span>
          Calls: <b>{trace.tool_calls.length}</b>
        </span>
        <span>
          Succeeded: <b>{succeeded}</b>
        </span>
        <span>
          Failed: <b>{failed}</b>
        </span>
        <span>
          Model: <b>{trace.model}</b>
        </span>
        <span>
          Time: <b>{(trace.total_duration_ms / 1000).toFixed(2)}s</b>
        </span>
      </div>

      {trace.grounding_check?.status === "PASSED" && (
        <div className="grounding-note ok">
          <strong>Grounding — passed.</strong>&nbsp; Every ID cited above appears in a real tool
          result.
        </div>
      )}
      {trace.grounding_check?.status === "FLAGGED" && (
        <div className="grounding-note flagged">
          <strong>Grounding — flagged.</strong>&nbsp; This answer references{" "}
          {trace.grounding_check.unrecognized_references.join(", ")} which wasn't found in any tool
          result — verify before relying on it.
        </div>
      )}

      <details className="raw-json-toggle">
        <summary>View raw trace JSON</summary>
        <pre className="json">{JSON.stringify(trace, null, 2)}</pre>
      </details>
    </div>
  );
}
