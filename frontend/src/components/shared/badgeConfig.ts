import type { ReportConclusion } from '../../types/report';
import type { RunStatus } from '../../types/run';

export const statusConfig: Record<RunStatus, { color: string; labelKey: string }> = {
  queued: { color: 'default', labelKey: 'status.queued' },
  running: { color: 'processing', labelKey: 'status.running' },
  succeeded: { color: 'success', labelKey: 'status.succeeded' },
  failed: { color: 'error', labelKey: 'status.failed' },
};

export const conclusionConfig: Record<ReportConclusion, { color: string; labelKey: string }> = {
  keep: { color: 'success', labelKey: 'conclusion.keep' },
  optimize: { color: 'warning', labelKey: 'conclusion.optimize' },
  fix: { color: 'error', labelKey: 'conclusion.fix' },
};
