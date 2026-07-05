import { Card, Typography, Spin, Result, Button, Badge, Tag } from 'antd';
import { FileSearchOutlined, ArrowLeftOutlined, CalendarOutlined } from '@ant-design/icons';
import { useNavigate, useParams, useSearchParams } from 'react-router';
import { useRunDetail } from '../hooks/useRunDetail';
import StatusBadge from '../components/shared/StatusBadge';
import StepTimeline from '../components/runs/StepTimeline';
import dayjs from 'dayjs';
import type { RunStatus } from '../types/run';

const { Text, Title } = Typography;

const statusLabels: Record<RunStatus, string> = {
  queued: '等待执行',
  running: '执行中',
  succeeded: '已完成',
  failed: '已失败',
};

export default function RunDetailPage() {
  const { runId } = useParams<{ runId: string }>();
  const [searchParams] = useSearchParams();
  const isDemo = searchParams.get('demo') === 'true';
  const navigate = useNavigate();

  const { statusQuery, stepsQuery } = useRunDetail(runId!, isDemo || undefined);

  const status = statusQuery.data;
  const steps = stepsQuery.data;

  if (statusQuery.isLoading) {
    return (
      <div className="loading-container">
        <Spin size="large" />
      </div>
    );
  }

  if (!status) {
    return <Result status="404" title="Run Not Found" subTitle="该运行记录不存在或已被删除" />;
  }

  const isFinished = status.status === 'succeeded' || status.status === 'failed';
  const displayId = runId && runId.length > 12 ? `${runId.slice(0, 12)}…` : runId || '';

  return (
    <div>
      {/* Header */}
      <div className="page-header" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/')}
            style={{ borderRadius: 8 }}
          />
          <Title level={1} style={{ margin: 0, fontSize: 24, fontWeight: 700, color: 'var(--color-text-primary)' }}>
            Run Detail
          </Title>
        </div>
      </div>

      {/* Status Card */}
      <Card
        className="demo-card"
        style={{ marginBottom: 24, borderRadius: 12, border: '1px solid var(--color-border)' }}
      >
        <div className="run-header" style={{ marginBottom: 12 }}>
          <StatusBadge status={status.status} />
          <Text style={{ fontSize: 14, color: 'var(--color-text-secondary)', fontWeight: 500 }}>
            {statusLabels[status.status]}
          </Text>
          <Tag style={{ fontSize: 12, borderRadius: 6, background: 'var(--color-bg)', border: '1px solid var(--color-border)' }}>
            {displayId}
          </Tag>
          <Text style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>
            <CalendarOutlined style={{ marginRight: 4 }} />
            {dayjs(status.created_at).format('YYYY-MM-DD HH:mm:ss')}
          </Text>

          <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
            {isFinished && (
              <Button
                type="primary"
                icon={<FileSearchOutlined />}
                onClick={() => navigate(`/runs/${runId}/report`)}
                className="btn-primary-gradient"
              >
                View Report
              </Button>
            )}
          </div>
        </div>

        {status.error_message && (
          <div className="error-card" style={{ marginTop: 16, textAlign: 'left' }}>
            <div className="error-icon">⚠️</div>
            <h4 style={{ margin: '0 0 4px 0', color: 'var(--color-error)', fontWeight: 600 }}>
              {status.error_type || 'Error'}
            </h4>
            <p style={{ margin: 0, color: '#666', fontSize: 13 }}>{status.error_message}</p>
          </div>
        )}
      </Card>

      {/* Steps Section */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
          <Title level={4} style={{ margin: 0, fontSize: 16, fontWeight: 600, color: 'var(--color-text-primary)' }}>
            Steps
          </Title>
          {steps && (
            <Badge
              count={steps.length}
              style={{
                backgroundColor: 'var(--color-bg)',
                color: 'var(--color-text-muted)',
                border: '1px solid var(--color-border)',
                borderRadius: 10,
                fontSize: 12,
                fontWeight: 600,
              }}
            />
          )}
        </div>

        {stepsQuery.isLoading ? (
          <div className="loading-container" style={{ minHeight: 100 }}>
            <Spin />
          </div>
        ) : steps && steps.length > 0 ? (
          <StepTimeline steps={steps} />
        ) : (
          <div className="empty-state" style={{ padding: 48 }}>
            <div className="empty-icon" style={{ fontSize: 40, marginBottom: 12 }}>📋</div>
            <h4 style={{ margin: '0 0 8px 0', fontSize: 15, fontWeight: 600, color: 'var(--color-text-primary)' }}>
              {status.status === 'queued' ? '等待执行...' : '暂无步骤数据'}
            </h4>
            {status.status === 'queued' && (
              <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: 14 }}>
                Run 已加入队列，执行开始后将显示步骤日志。
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
