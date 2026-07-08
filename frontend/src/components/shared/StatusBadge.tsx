import { Tag } from 'antd';
import type { RunStatus } from '../../types/run';
import { statusConfig } from './badgeConfig';
import { useTranslation } from 'react-i18next';

export default function StatusBadge({ status }: { status: RunStatus }) {
  const { t } = useTranslation();
  const cfg = statusConfig[status] ?? { color: 'default', labelKey: status };
  return <Tag color={cfg.color}>{t(cfg.labelKey)}</Tag>;
}
