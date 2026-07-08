import { Tag } from 'antd';
import type { ReportConclusion } from '../../types/report';
import { conclusionConfig } from './badgeConfig';
import { useTranslation } from 'react-i18next';

export default function ConclusionBadge({ conclusion }: { conclusion: ReportConclusion }) {
  const { t } = useTranslation();
  const cfg = conclusionConfig[conclusion] ?? { color: 'default', labelKey: conclusion };
  return <Tag color={cfg.color}>{t(cfg.labelKey)}</Tag>;
}
