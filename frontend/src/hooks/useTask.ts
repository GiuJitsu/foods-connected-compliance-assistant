import { useCallback, useEffect, useRef, useState } from "react";
import { getTask, submitTask } from "../api";
import type { TaskTrace } from "../types";

const POLL_INTERVAL_MS = 900;
const TERMINAL_STATUSES = new Set(["COMPLETED", "COMPLETED_PARTIAL", "FAILED"]);

/**
 * Submits a task, then polls GET /api/tasks/{id} until a terminal status
 * (CLAUDE.md "Backend API contract" — "poll this until status is COMPLETED /
 * COMPLETED_PARTIAL / FAILED"). AC2: the IN_PROGRESS state from the POST
 * response is rendered immediately, before the first poll ever resolves.
 */
export function useTask() {
  const [trace, setTrace] = useState<TaskTrace | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const pollTimeout = useRef<number | null>(null);
  const mounted = useRef(true);

  useEffect(() => {
    // Must reset to true on setup, not just false on cleanup: React
    // StrictMode double-invokes effects in dev (mount -> cleanup -> mount),
    // and without this line the cleanup's `mounted.current = false` would
    // stick permanently after that first simulated unmount, silently
    // killing every poll's first `if (!mounted.current) return` check
    // before it could ever schedule the next one — found live via the
    // Playwright run: the UI stuck on "In progress" forever after exactly
    // one poll, even though the backend had already finished the task.
    mounted.current = true;
    return () => {
      mounted.current = false;
      if (pollTimeout.current !== null) window.clearTimeout(pollTimeout.current);
    };
  }, []);

  const poll = useCallback((taskId: string) => {
    const tick = async () => {
      try {
        const next = await getTask(taskId);
        if (!mounted.current) return;
        setTrace(next);
        if (!TERMINAL_STATUSES.has(next.status)) {
          pollTimeout.current = window.setTimeout(tick, POLL_INTERVAL_MS);
        }
      } catch (err) {
        if (!mounted.current) return;
        setConnectionError(err instanceof Error ? err.message : "Lost contact with the backend.");
      }
    };
    void tick();
  }, []);

  const ask = useCallback(
    async (task: string) => {
      if (pollTimeout.current !== null) window.clearTimeout(pollTimeout.current);
      setConnectionError(null);
      setTrace(null);
      try {
        const submitted = await submitTask(task);
        setTrace({
          task_id: submitted.task_id,
          task_input: task,
          status: submitted.status,
          limit_hit: "NONE",
          tool_calls: [],
          final_answer: null,
          failure_reason: null,
          model: "",
          total_duration_ms: 0,
          grounding_check: null,
        });
        poll(submitted.task_id);
      } catch (err) {
        setConnectionError(err instanceof Error ? err.message : "Could not submit the task.");
      }
    },
    [poll],
  );

  const isBusy = trace !== null && !TERMINAL_STATUSES.has(trace.status);

  return { trace, connectionError, ask, isBusy };
}
