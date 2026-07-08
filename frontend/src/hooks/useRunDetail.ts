import { useQuery } from '@tanstack/react-query';
import * as api from '../api/runs';
import type { RunStatus } from '../types/run';
import { hasStatus } from '../lib/api-error';
import { useFrontendSettings } from './useFrontendSettings';

const isPolling = (status?: RunStatus) => status === 'queued' || status === 'running';

/**
 * 获取 run 详情，自动检测 demo/formal 类型。
 * 先尝试 formal run API，404 时自动 fallback 到 demo run API。
 *
 * 步骤轮询间隔与开关由 FrontendSettings.auto_refresh / refresh_interval_ms 驱动，
 * 让设置页的「自动刷新运行状态」「刷新间隔」真正生效。
 */
export function useRunDetail(runId: string, initialIsDemo?: boolean) {
  const { data: settings } = useFrontendSettings();
  const autoRefresh = settings?.auto_refresh ?? true;
  const refreshInterval = settings?.refresh_interval_ms ?? 3000;
  const stepsInterval = autoRefresh ? refreshInterval : false;
  const statusQuery = useQuery({
    queryKey: ['run-detail', runId, 'status'],
    queryFn: async () => {
      if (initialIsDemo) {
        return api.getDemoRunStatus(runId);
      }
      try {
        return await api.getRunStatus(runId);
      } catch (err: unknown) {
        // formal run 404 → fallback 到 demo run
        if (hasStatus(err, 404)) {
          return api.getDemoRunStatus(runId);
        }
        throw err;
      }
    },
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return isPolling(status) ? 2000 : false;
    },
  });

  const stepsQuery = useQuery({
    queryKey: ['run-detail', runId, 'steps'],
    queryFn: async () => {
      if (initialIsDemo) {
        return api.getDemoRunSteps(runId);
      }
      try {
        return await api.getRunSteps(runId);
      } catch (err: unknown) {
        if (hasStatus(err, 404)) {
          return api.getDemoRunSteps(runId);
        }
        throw err;
      }
    },
    refetchInterval: isPolling(statusQuery.data?.status) ? stepsInterval : false,
    enabled: !!statusQuery.data,
  });

  const reportQuery = useQuery({
    queryKey: ['run-detail', runId, 'report'],
    queryFn: async () => {
      if (initialIsDemo) {
        return api.getDemoRunReport(runId);
      }
      try {
        return await api.getRunReport(runId);
      } catch (err: unknown) {
        if (hasStatus(err, 404)) {
          return api.getDemoRunReport(runId);
        }
        throw err;
      }
    },
    enabled: statusQuery.data?.status === 'succeeded' || statusQuery.data?.status === 'failed',
    retry: 1,
  });

  return { statusQuery, stepsQuery, reportQuery };
}
