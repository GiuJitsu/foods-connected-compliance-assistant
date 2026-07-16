import { AnswerCard } from "./components/AnswerCard";
import { Banner } from "./components/Banner";
import { FailureCard } from "./components/FailureCard";
import { Sidebar } from "./components/Sidebar";
import { StatusBanner } from "./components/StatusBanner";
import { TraceList } from "./components/TraceList";
import { useTask } from "./hooks/useTask";

export default function App() {
  const { trace, connectionError, ask, isBusy } = useTask();

  return (
    <>
      <Banner onSubmit={ask} busy={isBusy} />

      <div className="shell">
        <Sidebar />

        <main>
          {connectionError && (
            <section>
              <div className="status-banner tone-failed">
                <span className="status-dot" />
                <span className="status-title">Could not reach the backend</span>
                <span className="status-sub">{connectionError}</span>
              </div>
            </section>
          )}

          {!trace && !connectionError && (
            <p className="empty-state">Ask a question above to see the agent's tool-call trace here.</p>
          )}

          {trace && (
            <>
              <section>
                <p className="section-label">Status</p>
                <StatusBanner trace={trace} />
              </section>

              <section>
                <p className="section-label">
                  Agent activity{trace.tool_calls.length > 0 ? ` — ${trace.tool_calls.length} call(s)` : ""}
                </p>
                <TraceList calls={trace.tool_calls} />
              </section>

              {(trace.status === "COMPLETED" || trace.status === "COMPLETED_PARTIAL") && (
                <section>
                  <p className="section-label">Answer</p>
                  <AnswerCard trace={trace} />
                </section>
              )}

              {trace.status === "FAILED" && (
                <section>
                  <p className="section-label">Answer</p>
                  <FailureCard trace={trace} />
                </section>
              )}
            </>
          )}
        </main>
      </div>
    </>
  );
}
