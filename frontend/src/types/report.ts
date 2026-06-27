import type { Persona } from './persona';
import type { Task, ActionName } from './task';
import type { RunStatus, RunErrorType } from './run';

export type ReportConclusion = 'keep' | 'optimize' | 'fix';
export type FrictionSeverity = 'low' | 'medium' | 'high';
export type ValidationStatus = 'running' | 'succeeded' | 'failed';
export type WaitObservationStatus = 'success' | 'actionable' | 'normal_timeout' | 'abnormal_stuck';
export type WaitObservationDecision = 'normal_waiting' | 'abnormal_stuck' | 'ready_for_next_action' | 'task_completed';

// ============================ Report ============================ #

export interface KeyScreenshot {
  label: string;
  step_index: number;
  path: string;
  source: 'before_action' | 'after_action' | 'wait_observation';
}

export interface FrictionIssue {
  signal: string;
  severity: FrictionSeverity;
  step_indexes: number[];
  description: string;
  suggested_fix: string;
}

export interface RunReport {
  run_id: string;
  status: RunStatus;
  summary: string;
  success: boolean;
  conclusion: ReportConclusion;
  persona: Persona;
  task: Task;
  total_steps: number;
  friction_signals: string[];
  friction_issues: FrictionIssue[];
  key_findings: string[];
  next_recommendations: string[];
  step_details: Record<string, unknown>[];
  structured_facts: Record<string, unknown> | null;
  key_screenshots: KeyScreenshot[];
  error_type?: RunErrorType | null;
  error_message?: string | null;
}

// ============================ Step ============================ #

export interface ObservedElement {
  text: string;
  selector: string;
}

export interface FormFieldState {
  name: string;
  selector: string;
  value: string;
}

export interface ObservedPageState {
  current_url: string;
  title: string;
  visible_text_summary: string;
  clickable_elements: ObservedElement[];
  form_fields: FormFieldState[];
  error_messages: string[];
  screenshot_path: string | null;
}

export interface ActionInput {
  action: ActionName;
  payload: Record<string, unknown>;
  reason: string;
}

export interface ExecutionResult {
  action: ActionName;
  success: boolean;
  detail: string;
  error_message?: string | null;
}

export interface ValidationResult {
  status: ValidationStatus;
  should_stop: boolean;
  progress_summary: string;
  friction_signals: string[];
  detected_success: boolean;
  detected_error: boolean;
}

export interface RetrievedContextItem {
  source_type: string;
  title: string;
  content: string;
  source_ref: string;
}

export interface StepLog {
  step_index: number;
  observed_page_state: ObservedPageState;
  decided_action: ActionInput;
  execution_result: ExecutionResult;
  validation_result: ValidationResult;
  post_action_page_state: ObservedPageState;
  wait_observation_status?: WaitObservationStatus | null;
  wait_observation_reason?: string | null;
  wait_observation_observations?: number | null;
  wait_observation_elapsed_ms?: number | null;
  wait_observation_timeout_ms?: number | null;
  wait_observation_terminal_decision?: WaitObservationDecision | null;
  wait_observation_traces?: Record<string, unknown>[];
  retrieval_context?: RetrievedContextItem[];
  before_page_state: ObservedPageState;
  after_page_state: ObservedPageState;
}
