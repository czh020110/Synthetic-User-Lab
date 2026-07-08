import type { Persona } from './persona';
import type { Task } from './task';

export type RunStatus = 'queued' | 'running' | 'succeeded' | 'failed';
export type RunErrorType = 'model_error' | 'system_error';

export interface RunStatusResponse {
  run_id: string;
  status: RunStatus;
  created_at: string;
  updated_at: string;
  error_type?: RunErrorType | null;
  error_message?: string | null;
}

export interface FormalRunRequest {
  persona_id: string;
  task_id: string;
  run_name?: string;
  headless?: boolean | null;
  max_steps_override?: number | null;
}

export interface RunRequest {
  run_name?: string;
  headless?: boolean | null;
}

export interface RunStartResponse {
  run_id: string;
  status: RunStatus;
}

export interface RunRecord {
  run_id: string;
  status: RunStatus;
  request: RunRequest;
  persona: Persona;
  task: Task;
  created_at: string;
  updated_at: string;
  error_type?: RunErrorType | null;
  error_message?: string | null;
}

export interface BatchRunRequest {
  task_id: string;
  persona_ids: string[];
  run_name?: string;
  headless?: boolean | null;
  max_steps_override?: number | null;
}

export interface BatchRunResponse {
  run_ids: string[];
  task_id: string;
}
