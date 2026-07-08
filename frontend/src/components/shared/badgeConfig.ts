import type { ReportConclusion } from '../../types/report';
import type { RunStatus } from '../../types/run';

export const statusConfig: Record<
  RunStatus,
  { dotClass: string; labelKey: string }
> = {
  queued: { dotClass: 'dot-muted', labelKey: 'status.queued' },
  running: { dotClass: 'dot-info', labelKey: 'status.running' },
  succeeded: { dotClass: 'dot-success', labelKey: 'status.succeeded' },
  failed: { dotClass: 'dot-error', labelKey: 'status.failed' },
};

export const conclusionConfig: Record<
  ReportConclusion,
  { dotClass: string; labelKey: string }
> = {
  keep: { dotClass: 'dot-success', labelKey: 'conclusion.keep' },
  optimize: { dotClass: 'dot-warning', labelKey: 'conclusion.optimize' },
  fix: { dotClass: 'dot-error', labelKey: 'conclusion.fix' },
};
