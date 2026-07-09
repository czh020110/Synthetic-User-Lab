import { useQuery } from '@tanstack/react-query';
import * as api from '../api/runs';

export function useRunReportMarkdown(runId: string) {
  return useQuery({
    queryKey: ['run-report-markdown', runId],
    queryFn: () => api.getRunReportMarkdown(runId),
    enabled: !!runId,
    retry: 1,
  });
}
