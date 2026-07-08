import { Card, Typography, Button, Badge, Tag, Space, Breadcrumb } from 'antd';
import { FileSearchOutlined, ArrowLeftOutlined, CalendarOutlined, ReloadOutlined } from '@ant-design/icons';
import { useNavigate, useParams, useSearchParams } from 'react-router';
import { useRunDetail } from '../hooks/useRunDetail';
import StatusBadge from '../components/shared/StatusBadge';
import StepTimeline from '../components/runs/StepTimeline';
import dayjs from 'dayjs';
import type { RunStatus } from '../types/run';
import { AppEmpty, AppErrorState, AppLoading } from '../components/feedback/AppFeedback';
import { getErrorMessage } from '../lib/api-error';

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

  const handleRefresh = () => {
    statusQuery.refetch();
    stepsQuery.refetch();
  };

  if (statusQuery.isLoading) {
    return <AppLoading tip="加载运行详情…" minHeight={260} />;
  }

  if (statusQuery.isError) {
    return (
      <AppErrorState
        title="无法加载运行详情"
        description={getErrorMessage(statusQuery.error, '请稍后重试')}
        onRetry={() => statusQuery.refetch()}
        extra={
          <Button type="primary" onClick={() => navigate('/')}>
            Back to Dashboard
          </Button>
        }
      />
    );
  }

  if (!status) {
    return (
      <AppEmpty
        title="Run Not Found"
        description="该运行记录不存在或已被删除。"
        action={
          <Button type="primary" onClick={() => navigate('/')}>
            Back to Dashboard
          </Button>
        }
      />
    );
  }

  const isFinished = status.status === 'succeeded' || status.status === 'failed';
  const isRunning = status.status === 'running';
  const isQueued = status.status === 'queued';
  const displayId = runId && runId.length > 12 ? `${runId.slice(0, 12)}…` : runId || '';

  return (
    <div>
      {/* Breadcrumb */}
      <Breadcrumb
        style={{ marginBottom: 16 }}
        items={[
          { title: <span style={{ cursor: 'pointer' }} onClick={() => navigate('/')}>Dashboard</span> },
          { title: <span>Run {displayId}</span> },
        ]}
      />

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
        <Text style={{ fontSize: 14, color: 'var(--color-text-muted)' }}>
          {isDemo ? 'Demo Run' : 'Formal Run'} — {statusLabels[status.status]}
        </Text>
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
            <Button
              icon={<ReloadOutlined />}
              onClick={handleRefresh}
              loading={statusQuery.isFetching || stepsQuery.isFetching}
            >
              Refresh
            </Button>
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

        {/* Progress indicator */}
        {(isRunning || isQueued) && (
          <div style={{ marginTop: 16, padding: 16, background: '#f6ffed', borderRadius: 8, border: '1px solid #b7eb8f' }}>
            <Space>
              <Text style={{ color: '#52c41a', fontWeight: 500 }}>
                {isRunning ? '执行中...步骤数据实时更新' : '等待执行...'}
              </Text>
            </Space>
          </div>
        )}
      </Card>

      {/* Steps Section */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16, justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
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
          <Button
            icon={<ReloadOutlined />}
            size="small"
            onClick={() => stepsQuery.refetch()}
            loading={stepsQuery.isFetching}
          >
            Refresh Steps
          </Button>
        </div>

        {stepsQuery.isLoading ? (
          <AppLoading tip="加载步骤日志…" minHeight={140} />
        ) : stepsQuery.isError ? (
          <AppErrorState
            title="无法加载步骤日志"
            description={getErrorMessage(stepsQuery.error, '请稍后重试')}
            onRetry={() => stepsQuery.refetch()}
          />
        ) : steps && steps.length > 0 ? (
          <StepTimeline steps={steps} />
        ) : (
          <AppEmpty
            title={status.status === 'queued' ? '等待执行...' : '暂无步骤数据'}
            description={status.status === 'queued' ? 'Run 已加入队列，执行开始后将显示步骤日志。' : '当前运行还没有可展示的步骤记录。'}
          />
        )}
      </div>
    </div>
  );
}
