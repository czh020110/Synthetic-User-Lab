import { Button, Empty, Result, Skeleton, Space, Typography } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';

const { Text, Title } = Typography;

type AppEmptyProps = {
  title: string;
  description?: ReactNode;
  action?: ReactNode;
  image?: ReactNode;
};

export function AppEmpty({ title, description, action, image }: AppEmptyProps) {
  return (
    <div className="app-feedback-shell app-feedback-empty">
      <Empty
        image={image ?? Empty.PRESENTED_IMAGE_SIMPLE}
        description={null}
      />
      <Title level={4} className="app-feedback-title">
        {title}
      </Title>
      {description ? <Text className="app-feedback-description">{description}</Text> : null}
      {action ? <div className="app-feedback-action">{action}</div> : null}
    </div>
  );
}

type AppErrorStateProps = {
  title: string;
  description?: ReactNode;
  onRetry?: () => void;
  extra?: ReactNode;
};

export function AppErrorState({ title, description, onRetry, extra }: AppErrorStateProps) {
  const { t } = useTranslation();

  return (
    <Result
      status="error"
      title={title}
      subTitle={description}
      extra={(
        <Space>
          {onRetry ? (
            <Button icon={<ReloadOutlined />} onClick={onRetry}>
              {t('common.retry')}
            </Button>
          ) : null}
          {extra}
        </Space>
      )}
    />
  );
}

type AppLoadingProps = {
  tip?: ReactNode;
  minHeight?: number;
};

export function AppLoading({ tip, minHeight = 220 }: AppLoadingProps) {
  return (
    <div className="app-feedback-shell app-feedback-loading" style={{ minHeight }}>
      <Skeleton active paragraph={{ rows: 4 }} style={{ width: '100%', maxWidth: 560 }} />
      {tip ? <Text className="app-feedback-description">{tip}</Text> : null}
    </div>
  );
}

type AppPageSkeletonProps = {
  cards?: number;
};

export function AppPageSkeleton({ cards = 3 }: AppPageSkeletonProps) {
  return (
    <div className="app-page-skeleton">
      <Skeleton.Input active size="large" style={{ width: 220, height: 28, marginBottom: 12 }} />
      <Skeleton.Input active size="small" style={{ width: 360, marginBottom: 24 }} />
      <div className="app-page-skeleton-grid">
        {Array.from({ length: cards }).map((_, index) => (
          <div className="app-page-skeleton-card" key={index}>
            <Skeleton active paragraph={{ rows: 4 }} />
          </div>
        ))}
      </div>
    </div>
  );
}
