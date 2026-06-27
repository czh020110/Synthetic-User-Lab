export type ActionName =
  | 'navigate' | 'click' | 'fill' | 'wait'
  | 'press' | 'scroll' | 'upload' | 'select'
  | 'hover' | 'check' | 'uncheck' | 'dblclick'
  | 'drag' | 'ask_for_help' | 'abandon';

export type RiskLevel = 'low' | 'medium' | 'high';

export interface Task {
  id: string;
  name: string;
  description: string;
  start_url: string;
  success_criteria: string[];
  max_steps: number;
  allowed_actions: ActionName[];
  risk_level: RiskLevel;
  destructive_action_allowed: boolean;
  created_at: string;
  updated_at: string;
}

export interface TaskCreate {
  name: string;
  description?: string;
  start_url: string;
  success_criteria?: string[];
  max_steps?: number;
  allowed_actions?: ActionName[];
  risk_level?: RiskLevel;
  destructive_action_allowed?: boolean;
}

export interface TaskUpdate {
  name?: string | null;
  description?: string | null;
  start_url?: string | null;
  success_criteria?: string[] | null;
  max_steps?: number | null;
  allowed_actions?: ActionName[] | null;
  risk_level?: RiskLevel | null;
  destructive_action_allowed?: boolean | null;
}
