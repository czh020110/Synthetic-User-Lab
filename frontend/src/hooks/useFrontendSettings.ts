import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as api from '../api/settings';
import type { FrontendSettingsUpdate } from '../types/settings';

export function useFrontendSettings() {
  return useQuery({
    queryKey: ['frontend-settings'],
    queryFn: api.getFrontendSettings,
    // AppProviders 与 SettingsPage 各自处理失败（回退默认值 / 内联 Alert），
    // 抑制全局 QueryCache.onError 的重复 toast。
    meta: { silentError: true } as { silentError: boolean },
  });
}

export function useUpdateFrontendSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: FrontendSettingsUpdate) => api.updateFrontendSettings(data),
    onSuccess: (settings) => {
      qc.setQueryData(['frontend-settings'], settings);
    },
  });
}
