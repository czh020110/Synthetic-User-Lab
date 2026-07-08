import type { ReportConclusion } from '../../types/report';
import { conclusionConfig } from './badgeConfig';
import { useTranslation } from 'react-i18next';

export default function ConclusionBadge({ conclusion }: { conclusion: ReportConclusion }) {
  const { t } = useTranslation();
  const cfg = conclusionConfig[conclusion] ?? { dotClass: 'dot-muted', labelKey: conclusion };
  return (
    <span className={`status-dot ${cfg.dotClass}`}>
      {t(cfg.labelKey)}
    </span>
  );
}
