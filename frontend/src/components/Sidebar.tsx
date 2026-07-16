import { useEffect, useState } from "react";
import { getInfo } from "../api";
import type { AgentInfo } from "../types";

/** ZONE 1: static "how this agent works" panel (AC12) — always visible,
 * fetched once at load, not per-task. */
export function Sidebar() {
  const [info, setInfo] = useState<AgentInfo | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    getInfo()
      .then(setInfo)
      .catch(() => setFailed(true));
  }, []);

  return (
    <aside className="sidebar">
      <p className="board-title">How this agent works</p>

      <div className="board-block">
        <p className="board-label">Model</p>
        <p className="board-value">{info ? info.model : failed ? "unavailable" : "loading…"}</p>
      </div>

      <div className="board-block">
        <p className="board-label">Tools available</p>
        <ul className="board-tools">
          {info?.tools.map((tool) => (
            <li key={tool.name} title={tool.description}>
              {tool.name}
            </li>
          ))}
          {!info && <li className="board-tools-empty">{failed ? "unavailable" : "loading…"}</li>}
        </ul>
      </div>

      <div className="board-block">
        <p className="board-label">Hard limits</p>
        <div className="board-limits">
          <span>
            <b>{info?.iteration_cap ?? "—"}</b> tool calls max
          </span>
          <span>
            <b>{info ? `${info.per_call_timeout_s}s` : "—"}</b> per call
          </span>
          <span>
            <b>{info ? `${info.total_timeout_s}s` : "—"}</b> total per task
          </span>
        </div>
      </div>
    </aside>
  );
}
