import { useQuery } from '@tanstack/react-query';
import * as api from '../api/runs';
import type { RunStatus } from '../types/run';

const isPolling = (status?: RunStatus) => status === 'queued' || status === 'running';

/**
 * 获取 run 详情，自动检测 demo/formal 类型。
 * 先尝试 formal run API，404 时自动 fallback 到 demo run API。
 */
export function useRunDetail(runId: string, initialIsDemo?: boolean) {
  const statusQuery = useQuery({
    queryKey: ['run-detail', runId, 'status'],
    queryFn: async () => {
      if (initialIsDemo) {
        return api.getDemoRunStatus(runId);
      }
      try {
        return await api.getRunStatus(runId);
      } catch (err: any) {
        // formal run 404 → fallback 到 demo run
        if (err?.response?.status === 404) {
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
      } catch (err: any) {
        if (err?.response?.status === 404) {
          return api.getDemoRunSteps(runId);
        }
        throw err;
      }
    },
    refetchInterval: isPolling(statusQuery.data?.status) ? 3000 : false,
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
      } catch (err: any) {
        if (err?.response?.status === 404) {
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
