import { theme } from 'antd';
import type { ThemeConfig } from 'antd';
import type { ThemeMode } from './types/settings';

const { defaultAlgorithm, darkAlgorithm } = theme;

export function resolveThemeMode(mode: ThemeMode): Exclude<ThemeMode, 'auto'> {
  if (mode !== 'auto') {
    return mode;
  }
  if (typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }
  return 'light';
}

export function buildThemeConfig(mode: ThemeMode): ThemeConfig {
  const resolved = resolveThemeMode(mode);
  return {
    algorithm: resolved === 'dark' ? darkAlgorithm : defaultAlgorithm,
    token: {
      colorPrimary: '#1677FF',
      borderRadius: 10,
    },
  };
}
