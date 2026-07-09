import { useQuery } from '@tanstack/react-query';
import * as api from '../api/runs';
import type { RunStatus } from '../types/run';
import { useFrontendSettings } from './useFrontendSettings';

const isPolling = (status?: RunStatus) => status === 'queued' || status === 'running';

/**
 * 获取 run 详情（status / steps / report）。
 *
 * 步骤轮询间隔与开关由 FrontendSettings.auto_refresh / refresh_interval_ms 驱动，
 * 让设置页的「自动刷新运行状态」「刷新间隔」真正生效。
 */
export function useRunDetail(runId: string) {
  const { data: settings } = useFrontendSettings();
  const autoRefresh = settings?.auto_refresh ?? true;
  const refreshInterval = settings?.refresh_interval_ms ?? 3000;
  const stepsInterval = autoRefresh ? refreshInterval : false;

  const statusQuery = useQuery({
    queryKey: ['run-detail', runId, 'status'],
    queryFn: () => api.getRunStatus(runId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return isPolling(status) ? 2000 : false;
    },
  });

  const stepsQuery = useQuery({
    queryKey: ['run-detail', runId, 'steps'],
    queryFn: () => api.getRunSteps(runId),
    refetchInterval: isPolling(statusQuery.data?.status) ? stepsInterval : false,
    enabled: !!statusQuery.data,
  });

  const reportQuery = useQuery({
    queryKey: ['run-detail', runId, 'report'],
    queryFn: () => api.getRunReport(runId),
    enabled: statusQuery.data?.status === 'succeeded' || statusQuery.data?.status === 'failed',
    retry: 1,
  });

  return { statusQuery, stepsQuery, reportQuery };
}
