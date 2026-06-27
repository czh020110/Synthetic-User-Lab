import { useQuery } from '@tanstack/react-query';
import * as api from '../api/runs';
import type { RunStatus } from '../types/run';

const isPolling = (status?: RunStatus) => status === 'queued' || status === 'running';

/**
 * 获取 run 详情，自动检测 demo/formal 类型。
 * 先尝试 formal run API，404 时自动 fallback 到 demo run API。
 */
export function useRunDetail(runId: string, initialIsDemo?: boolean) {
  // 先用 formal API 尝试；如果 initialIsDemo 已知为 true 则直接用 demo
  const statusQuery = useQuery({
    queryKey: ['run-detail', runId, 'status'],
    queryFn: async () => {
      if (initialIsDemo) {
        return api.getDemoRunStatus(runId);
      }
      try {
        return await api.getRunStatus(runId);
      } catch (err) {
        // formal run 404 → fallback 到 demo run
        if (err instanceof Error && err.message.includes('not found')) {
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

  const resolvedIsDemo = initialIsDemo ?? (() => {
    // 如果 formal API 返回了数据，说明不是 demo run
    // 如果 fallback 到了 demo API，queryKey 不变但数据来自 demo
    // 通过 queryKey 中的信息无法判断，所以用函数内闭包变量
    return false; // 默认 formal，fallback 在 queryFn 中已处理
  })();

  // 使用 statusQuery 数据判断是否走 demo 路径
  // 更简洁的方案：统一用同一套 queryKey，根据 queryFn 中的 fallback 结果选择 steps/report 端点
  const isDemoRun = initialIsDemo === true;

  const stepsQuery = useQuery({
    queryKey: ['run-detail', runId, 'steps'],
    queryFn: async () => {
      if (initialIsDemo) {
        return api.getDemoRunSteps(runId);
      }
      try {
        return await api.getRunSteps(runId);
      } catch (err) {
        if (err instanceof Error && err.message.includes('not found')) {
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
      } catch (err) {
        if (err instanceof Error && err.message.includes('not found')) {
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
