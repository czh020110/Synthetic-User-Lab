import { Tag } from 'antd';
import type { ReportConclusion } from '../../types/report';

export const conclusionConfig: Record<ReportConclusion, { color: string; label: string }> = {
  keep: { color: 'success', label: 'Keep' },
  optimize: { color: 'warning', label: 'Optimize' },
  fix: { color: 'error', label: 'Fix' },
};

export default function ConclusionBadge({ conclusion }: { conclusion: ReportConclusion }) {
  const cfg = conclusionConfig[conclusion] ?? { color: 'default', label: conclusion };
  return <Tag color={cfg.color}>{cfg.label}</Tag>;
}
