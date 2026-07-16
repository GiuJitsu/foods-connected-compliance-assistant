/**
 * Mirrors backend/schemas.py exactly (field names, enum values). This is the
 * wire contract — keep in lockstep with the backend, not a frontend-only
 * convenience shape.
 */

export type TaskStatus = "IN_PROGRESS" | "COMPLETED" | "COMPLETED_PARTIAL" | "FAILED";

export type LimitHit = "NONE" | "ITERATION_CAP" | "TIMEOUT";

export type ToolErrorType = "VALIDATION_ERROR" | "NOT_FOUND" | "TIMEOUT" | "SERVER_ERROR";

export type FailureReason = "MCP_UNREACHABLE" | "MODEL_API_FAILURE" | "INTERNAL_ERROR";

export type GroundingStatus = "PASSED" | "FLAGGED";

export interface ToolCallError {
  type: ToolErrorType;
  message: string;
}

export interface ToolCallTrace {
  timestamp: string;
  tool_name: string;
  input: Record<string, unknown>;
  reasoning: string;
  thinking: string | null;
  result_summary: string;
  success: boolean;
  error: ToolCallError | null;
  latency_ms: number;
}

export interface GroundingCheck {
  status: GroundingStatus;
  unrecognized_references: string[];
}

export interface TaskTrace {
  task_id: string;
  task_input: string;
  status: TaskStatus;
  limit_hit: LimitHit;
  tool_calls: ToolCallTrace[];
  final_answer: string | null;
  failure_reason: FailureReason | null;
  model: string;
  total_duration_ms: number;
  grounding_check: GroundingCheck | null;
}

export interface TaskSubmitResponse {
  task_id: string;
  status: TaskStatus;
}

export interface ToolCatalogEntry {
  name: string;
  description: string;
}

export interface AgentInfo {
  model: string;
  tools: ToolCatalogEntry[];
  iteration_cap: number;
  per_call_timeout_s: number;
  total_timeout_s: number;
}
