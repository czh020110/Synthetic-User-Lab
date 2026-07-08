export type ThemeMode = 'light' | 'dark' | 'auto';
export type LocaleCode = 'zh-CN' | 'en-US';

export interface FrontendSettings {
  settings_key: string;
  theme: ThemeMode;
  locale: LocaleCode;
  timezone: string;
  date_format: string;
  default_headless: boolean;
  auto_refresh: boolean;
  refresh_interval_ms: number;
  default_run_name: string;
  default_max_steps: number;
  email_notifications: boolean;
  notify_run_complete: boolean;
  notify_run_failed: boolean;
  notify_system_error: boolean;
  created_at: string;
  updated_at: string;
}

export interface FrontendSettingsUpdate {
  theme?: ThemeMode;
  locale?: LocaleCode;
  timezone?: string;
  date_format?: string;
  default_headless?: boolean;
  auto_refresh?: boolean;
  refresh_interval_ms?: number;
  default_run_name?: string;
  default_max_steps?: number;
  email_notifications?: boolean;
  notify_run_complete?: boolean;
  notify_run_failed?: boolean;
  notify_system_error?: boolean;
}

export const DEFAULT_FRONTEND_SETTINGS: FrontendSettings = {
  settings_key: 'frontend',
  theme: 'light',
  locale: 'zh-CN',
  timezone: 'UTC',
  date_format: 'YYYY-MM-DD',
  default_headless: true,
  auto_refresh: true,
  refresh_interval_ms: 5000,
  default_run_name: 'run',
  default_max_steps: 30,
  email_notifications: true,
  notify_run_complete: true,
  notify_run_failed: true,
  notify_system_error: true,
  created_at: '',
  updated_at: '',
};
