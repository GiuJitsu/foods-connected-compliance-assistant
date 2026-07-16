/**
 * Fetch client for the backend API contract (CLAUDE.md "Backend API contract").
 * Every failure here (network down, non-2xx) is surfaced as a thrown Error
 * with a readable message — the caller decides how to render it. Never
 * exposes a raw stack trace to the UI (hard constraint #5).
 */

import type { AgentInfo, TaskSubmitResponse, TaskTrace } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    throw new Error("Could not reach the backend. Is it running?");
  }

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = (await res.json()) as { detail?: string };
      detail = body.detail ?? detail;
    } catch {
      // response body wasn't JSON — keep statusText
    }
    throw new Error(`${res.status}: ${detail}`);
  }

  return res.json() as Promise<T>;
}

export function submitTask(task: string): Promise<TaskSubmitResponse> {
  return request<TaskSubmitResponse>("/api/tasks", {
    method: "POST",
    body: JSON.stringify({ task }),
  });
}

export function getTask(taskId: string): Promise<TaskTrace> {
  return request<TaskTrace>(`/api/tasks/${taskId}`);
}

export function getInfo(): Promise<AgentInfo> {
  return request<AgentInfo>("/api/info");
}
