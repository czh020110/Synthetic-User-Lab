import { useQuery } from '@tanstack/react-query';
import * as api from '../api/runs';

export function useRunReportMarkdown(runId: string, isDemo?: boolean) {
  return useQuery({
    queryKey: ['run-report-markdown', runId, isDemo],
    queryFn: async () => {
      if (isDemo) {
        return api.getDemoRunReportMarkdown(runId);
      }
      try {
        return await api.getRunReportMarkdown(runId);
      } catch (err: any) {
        if (err?.response?.status === 404) {
          return api.getDemoRunReportMarkdown(runId);
        }
        throw err;
      }
    },
    enabled: !!runId,
    retry: 1,
  });
}
