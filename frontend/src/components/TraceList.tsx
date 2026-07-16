import type { ToolCallTrace, ToolErrorType } from "../types";

function stripeClass(errorType: ToolErrorType | undefined): string {
  switch (errorType) {
    case "TIMEOUT":
      return "err-timeout";
    case "SERVER_ERROR":
      return "err-server";
    case "VALIDATION_ERROR":
      return "err-validation";
    case "NOT_FOUND":
      return "err-notfound";
    default:
      return "";
  }
}

function chipClass(errorType: ToolErrorType | undefined): string {
  switch (errorType) {
    case "TIMEOUT":
      return "timeout";
    case "SERVER_ERROR":
      return "server";
    case "VALIDATION_ERROR":
      return "validation";
    case "NOT_FOUND":
      return "notfound";
    default:
      return "ok";
  }
}

function formatTime(iso: string): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleTimeString();
}

/** ZONE 4: the ordered tool-call trace. AC3 (success entries), AC4 (error
 * entries — 4 categories, each visually distinct, per CLAUDE.md "a validation
 * failure must look visually distinct from a timeout ... from a not-found"),
 * AC10 (reasoning), AC14 (collapsed thinking disclosure with fixed caption). */
export function TraceList({ calls }: { calls: ToolCallTrace[] }) {
  if (calls.length === 0) {
    return <p className="trace-empty">No tool calls yet.</p>;
  }

  return (
    <div className="trace-list">
      {calls.map((call, index) => {
        const errorType = call.error?.type;
        return (
          <div key={`${call.tool_name}-${index}`} className={`trace-entry ${stripeClass(errorType)}`}>
            <div className="trace-stripe" />
            <div className="trace-body">
              <div className="trace-top">
                <span className="trace-tool">
                  <span className="idx">{index + 1}</span>
                  {call.tool_name}
                </span>
                <span className="trace-meta">
                  {call.latency_ms}ms · {formatTime(call.timestamp)}
                </span>
              </div>

              <div className="trace-input">{JSON.stringify(call.input)}</div>

              <p className="trace-reasoning">
                <span className="rlabel">Reasoning</span>
                {call.reasoning}
              </p>

              <p className="trace-result">
                <span className={`status-chip ${chipClass(errorType)}`}>
                  {errorType ? errorType.toLowerCase() : "ok"}
                </span>
                &nbsp; {call.error ? call.error.message : call.result_summary}
              </p>

              {call.thinking && (
                <details className="thinking">
                  <summary>Extended thinking</summary>
                  <div className="thinking-body">
                    {call.thinking}
                    <span className="thinking-caption">
                      The model's own unedited reasoning for this step — not guaranteed to be a
                      complete or authoritative account of why it acted.
                    </span>
                  </div>
                </details>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
