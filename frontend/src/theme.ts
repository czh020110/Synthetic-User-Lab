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
  const isDark = resolved === 'dark';

  return {
    algorithm: isDark ? darkAlgorithm : defaultAlgorithm,
    token: {
      colorPrimary: isDark ? '#fafafa' : '#000000',
      colorBgContainer: isDark ? '#000000' : '#ffffff',
      colorBgLayout: isDark ? '#000000' : '#ffffff',
      colorBorder: isDark ? '#333333' : '#e5e5e5',
      colorText: isDark ? '#ffffff' : '#000000',
      colorTextSecondary: isDark ? '#888888' : '#666666',
      borderRadius: 5,
      borderRadiusLG: 8,
      borderRadiusSM: 4,
      fontFamily:
        '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      fontSize: 14,
      controlHeight: 36,
      lineHeight: 1.5,
    },
    components: {
      Button: {
        borderRadius: 5,
        controlHeight: 36,
        paddingInline: 16,
        primaryShadow: 'none',
        algorithm: true,
      },
      Card: {
        borderRadiusLG: 8,
        paddingLG: 24,
      },
      Table: {
        borderRadius: 8,
        headerBg: isDark ? '#0a0a0a' : '#fafafa',
        headerColor: isDark ? '#888888' : '#666666',
        borderColor: isDark ? '#222222' : '#f0f0f0',
        rowHoverBg: isDark ? '#0a0a0a' : '#fafafa',
      },
      Menu: {
        itemBorderRadius: 5,
        itemHeight: 36,
        iconSize: 16,
        collapsedWidth: 64,
        darkItemBg: 'transparent',
        darkItemHoverBg: 'rgba(255,255,255,0.06)',
        darkItemSelectedBg: 'rgba(255,255,255,0.1)',
      },
      Select: {
        borderRadius: 5,
        controlHeight: 36,
      },
      Input: {
        borderRadius: 5,
        controlHeight: 36,
      },
      Tag: {
        borderRadiusSM: 4,
      },
      Tabs: {
        cardGutter: 0,
      },
    },
  };
}
