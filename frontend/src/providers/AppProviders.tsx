import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import enUS from 'antd/locale/en_US';
import type { PropsWithChildren } from 'react';
import { useEffect } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import 'dayjs/locale/en';
import AppErrorBoundary from '../components/errors/AppErrorBoundary';
import { queryClient } from '../lib/queryClient';
import { useFrontendSettings } from '../hooks/useFrontendSettings';
import { DEFAULT_FRONTEND_SETTINGS } from '../types/settings';
import { buildThemeConfig, resolveThemeMode } from '../theme';

const localeMap = {
  'zh-CN': zhCN,
  'en-US': enUS,
} as const;

const dayjsLocaleMap = {
  'zh-CN': 'zh-cn',
  'en-US': 'en',
} as const;

function AppProvidersInner({ children }: PropsWithChildren) {
  const { data: settings } = useFrontendSettings();
  const mergedSettings = settings ?? DEFAULT_FRONTEND_SETTINGS;
  const { i18n } = useTranslation();

  useEffect(() => {
    if (i18n.language !== mergedSettings.locale) {
      void i18n.changeLanguage(mergedSettings.locale);
    }
    dayjs.locale(dayjsLocaleMap[mergedSettings.locale]);
    document.body.classList.toggle('theme-dark', resolveThemeMode(mergedSettings.theme) === 'dark');
  }, [i18n, mergedSettings.locale, mergedSettings.theme]);

  return (
    <ConfigProvider
      locale={localeMap[mergedSettings.locale]}
      theme={buildThemeConfig(mergedSettings.theme)}
    >
      <AppErrorBoundary>{children}</AppErrorBoundary>
    </ConfigProvider>
  );
}

export default function AppProviders({ children }: PropsWithChildren) {
  return (
    <QueryClientProvider client={queryClient}>
      <AppProvidersInner>{children}</AppProvidersInner>
    </QueryClientProvider>
  );
}
