import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '../api/runs';
import type { BatchRunRequest, FormalRunRequest, RunRequest } from '../types/run';

export function useRuns() {
  return useQuery({
    queryKey: ['runs'],
    queryFn: api.listRuns,
    select: (data) => data ?? [],
  });
}

export function useStartFormalRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: FormalRunRequest) => api.startFormalRun(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['runs'] }),
  });
}

export function useStartBatchRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: BatchRunRequest) => api.startBatchRun(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['runs'] }),
  });
}

export function useStartDemoRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data?: RunRequest) => api.startDemoRun(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['runs'] }),
  });
}
