import type { RunStatus } from '../../types/run';
import { statusConfig } from './badgeConfig';
import { useTranslation } from 'react-i18next';

export default function StatusBadge({ status }: { status: RunStatus }) {
  const { t } = useTranslation();
  const cfg = statusConfig[status] ?? { dotClass: 'dot-muted', labelKey: status };
  return (
    <span className={`status-dot ${cfg.dotClass}`}>
      {t(cfg.labelKey)}
    </span>
  );
}
