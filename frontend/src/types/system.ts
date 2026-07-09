export type ModelProvider = 'openai' | 'dashscope';

export interface ModelPreset {
  id: string;
  name: string;
  provider: ModelProvider;
  api_key: string;
  base_url: string;
  model_name: string;
  fast_model_name: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface ModelPresetCreate {
  name: string;
  provider: ModelProvider;
  api_key?: string;
  base_url?: string;
  model_name: string;
  fast_model_name?: string;
  is_default?: boolean;
}

export interface ModelPresetUpdate {
  name?: string;
  provider?: ModelProvider;
  api_key?: string;
  base_url?: string;
  model_name?: string;
  fast_model_name?: string;
}

export interface GuardConfig {
  settings_key: string;
  destructive_keywords: string[];
  sensitive_keywords: string[];
  created_at: string;
  updated_at: string;
}

export interface GuardConfigUpdate {
  destructive_keywords?: string[];
  sensitive_keywords?: string[];
}
