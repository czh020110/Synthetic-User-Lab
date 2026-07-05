import client from './client';
import type { RunStatusResponse, RunStartResponse, FormalRunRequest, RunRequest, BatchRunRequest, BatchRunResponse } from '../types/run';
import type { StepLog, RunReport, CompareReport } from '../types/report';

// ============================ Formal Runs ============================ //

export function startFormalRun(data: FormalRunRequest): Promise<RunStartResponse> {
  return client.post('/runs/start', data);
}

export function startBatchRun(data: BatchRunRequest): Promise<BatchRunResponse> {
  return client.post('/runs/batch', data);
}

export function compareRuns(runIds: string[]): Promise<CompareReport> {
  return client.post('/runs/compare', { run_ids: runIds });
}

export function listRuns(): Promise<RunStatusResponse[]> {
  return client.get('/runs/');
}

export function getRunStatus(runId: string): Promise<RunStatusResponse> {
  return client.get(`/runs/${runId}`);
}

export function getRunSteps(runId: string): Promise<StepLog[]> {
  return client.get(`/runs/${runId}/steps`);
}

export function getRunReport(runId: string): Promise<RunReport> {
  return client.get(`/runs/${runId}/report`);
}

export function getRunReportMarkdown(runId: string): Promise<{ markdown: string }> {
  return client.get(`/runs/${runId}/report/markdown`);
}

// ============================ Demo Runs ============================ //

export function startDemoRun(data?: RunRequest): Promise<RunStartResponse> {
  return client.post('/runs/demo/start', data || {});
}

export function getDemoRunStatus(runId: string): Promise<RunStatusResponse> {
  return client.get(`/runs/demo/${runId}`);
}

export function getDemoRunSteps(runId: string): Promise<StepLog[]> {
  return client.get(`/runs/demo/${runId}/steps`);
}

export function getDemoRunReport(runId: string): Promise<RunReport> {
  return client.get(`/runs/demo/${runId}/report`);
}

export function getDemoRunReportMarkdown(runId: string): Promise<{ markdown: string }> {
  return client.get(`/runs/demo/${runId}/report/markdown`);
}
