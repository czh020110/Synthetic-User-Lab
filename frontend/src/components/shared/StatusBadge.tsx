import { Tag } from 'antd';
import type { RunStatus } from '../../types/run';

const statusConfig: Record<RunStatus, { color: string; label: string }> = {
  queued: { color: 'default', label: 'Queued' },
  running: { color: 'processing', label: 'Running' },
  succeeded: { color: 'success', label: 'Succeeded' },
  failed: { color: 'error', label: 'Failed' },
};

export default function StatusBadge({ status }: { status: RunStatus }) {
  const cfg = statusConfig[status] ?? { color: 'default', label: status };
  return <Tag color={cfg.color}>{cfg.label}</Tag>;
}
