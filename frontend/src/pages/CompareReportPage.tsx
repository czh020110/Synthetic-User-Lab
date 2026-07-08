import { Card, Table, Typography, Row, Col, Progress, Space, Button } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate, useSearchParams } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import * as api from '../api/runs';
import ConclusionBadge from '../components/shared/ConclusionBadge';
import type { RunStatusResponse } from '../types/run';
import type { CompareItem, CompareReport, ReportConclusion } from '../types/report';
import { AppEmpty, AppErrorState, AppLoading } from '../components/feedback/AppFeedback';
import { getErrorMessage } from '../lib/api-error';

const { Title, Text } = Typography;

function isTerminal(status?: string) {
  return status === 'succeeded' || status === 'failed';
}

function shouldRetryCompare(failureCount: number, error: unknown): boolean {
  if (failureCount >= 1) return false;
  const msg = (error as Error)?.message || '';
  return !/not found|not finished|belongs to task/i.test(msg);
}

export default function CompareReportPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { t } = useTranslation();
  const idsParam = searchParams.get('ids') || '';
  const runIds = idsParam ? idsParam.split(',').filter(Boolean) : [];

  const pollQuery = useQuery({
    queryKey: ['compare-poll', runIds],
    queryFn: async (): Promise<(RunStatusResponse | null)[]> => {
      const all = await api.listRuns();
      const byId = new Map(all.map((s) => [s.run_id, s]));
      return runIds.map((id) => byId.get(id) ?? null);
    },
    enabled: runIds.length >= 2,
    refetchInterval: (query) => {
      if (query.state.error) return false;
      const statuses = query.state.data;
      if (!statuses) return 2000;
      return statuses.every((s) => s !== null && isTerminal(s.status)) ? false : 2000;
    },
  });

  const statuses = pollQuery.data;
  const missingCount = statuses?.filter((s) => s === null).length ?? 0;
  const allDone = !!statuses && statuses.every((s) => s !== null && isTerminal(s.status));
  const doneCount = statuses?.filter((s) => s !== null && isTerminal(s.status)).length ?? 0;

  const compareQuery = useQuery({
    queryKey: ['compare-report', runIds],
    queryFn: () => api.compareRuns(runIds),
    enabled: allDone,
    retry: shouldRetryCompare,
  });

  if (runIds.length < 2) {
    return (
      <AppEmpty
        title={t('compare.needTwoRunsTitle')}
        description={t('compare.needTwoRunsDescription')}
        action={
          <Button type="primary" onClick={() => navigate('/runs/new')}>
            {t('compare.goStartRun')}
          </Button>
        }
      />
    );
  }

  if (pollQuery.isError || (statuses && missingCount > 0)) {
    const missingMsg = statuses && missingCount > 0 ? `${missingCount} 个 run 不存在或已被清除` : undefined;
    return (
      <div>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/')} style={{ marginBottom: 16 }}>
          {t('common.back')}
        </Button>
        <AppErrorState
          title={t('compare.statusLoadFailed')}
          description={missingMsg || getErrorMessage(pollQuery.error, t('common.retryLater'))}
          onRetry={() => pollQuery.refetch()}
        />
      </div>
    );
  }

  if (!allDone) {
    return (
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/')} />
          <Title level={1} className="page-title">{t('compare.title')}</Title>
        </div>
        <Card className="demo-card">
          <div style={{ textAlign: 'center', padding: 48 }}>
            <AppLoading tip={`${t('compare.waitingAllDone')} ${doneCount} / ${runIds.length} ${t('compare.completedCount')}`} minHeight={160} />
            <Progress
              percent={Math.round((doneCount / runIds.length) * 100)}
              style={{ maxWidth: 400, margin: '16px auto 0' }}
            />
          </div>
        </Card>
      </div>
    );
  }

  if (compareQuery.isLoading) {
    return <AppLoading tip={t('compare.generating')} minHeight={240} />;
  }

  if (compareQuery.isError || !compareQuery.data) {
    return (
      <div>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/')} style={{ marginBottom: 16 }}>
          {t('common.back')}
        </Button>
        <AppErrorState
          title={t('compare.reportCreateFailed')}
          description={getErrorMessage(compareQuery.error, t('common.retryLater'))}
          onRetry={() => compareQuery.refetch()}
        />
      </div>
    );
  }

  const report: CompareReport = compareQuery.data;

  const columns: ColumnsType<CompareItem> = [
    {
      title: t('compare.columns.persona'),
      dataIndex: 'persona',
      render: (_, item) => item.persona.name,
    },
    {
      title: t('compare.columns.conclusion'),
      dataIndex: 'conclusion',
      render: (c: ReportConclusion) => <ConclusionBadge conclusion={c} />,
    },
    {
      title: t('compare.columns.result'),
      dataIndex: 'success',
      render: (s: boolean) => (
        <span className={`status-dot ${s ? 'dot-success' : 'dot-error'}`}>
          {s ? t('compare.resultSuccess') : t('compare.resultFailed')}
        </span>
      ),
    },
    {
      title: t('compare.columns.steps'),
      dataIndex: 'total_steps',
      sorter: (a, b) => a.total_steps - b.total_steps,
    },
    {
      title: t('compare.columns.friction'),
      dataIndex: 'friction_signal_count',
      sorter: (a, b) => a.friction_signal_count - b.friction_signal_count,
    },
    {
      title: t('compare.columns.summary'),
      dataIndex: 'summary',
      ellipsis: true,
    },
    {
      title: t('compare.columns.action'),
      render: (_, item) => (
        <Button type="link" size="small" onClick={() => navigate(`/runs/${item.run_id}`)}>{t('compare.actionViewDetail')}</Button>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/')} />
        <Title level={1} className="page-title">
          {t('compare.title')}
        </Title>
      </div>
      <Text style={{ fontSize: 13, color: 'var(--geist-foreground-tertiary)', display: 'block', marginBottom: 24 }}>
        任务：{report.task.name} · {report.comparison_summary}
      </Text>

      <Row gutter={12} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <div className="stat-card">
            <Text className="stat-value">{report.run_count}</Text>
            <Text className="stat-label">{t('compare.participants')}</Text>
          </div>
        </Col>
        <Col span={6}>
          <div className="stat-card">
            <Text className="stat-value">{report.success_count}<Text style={{ fontSize: 14, color: 'var(--geist-foreground-tertiary)', fontWeight: 400 }}>/{report.run_count}</Text></Text>
            <Text className="stat-label">{t('compare.success')}</Text>
          </div>
        </Col>
        <Col span={6}>
          <div className="stat-card">
            <Text className="stat-value">{report.avg_steps.toFixed(1)}</Text>
            <Text className="stat-label">{t('compare.avgSteps')}</Text>
          </div>
        </Col>
        <Col span={6}>
          <div className="stat-card">
            <Text className="stat-value">{report.total_friction_signals}</Text>
            <Text className="stat-label">{t('compare.totalFriction')}</Text>
          </div>
        </Col>
      </Row>

      <Card className="demo-card">
        <div style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 12 }}>
          <Text strong style={{ fontSize: 13 }}>{t('compare.distribution')}</Text>
          <Space>
            {Object.entries(report.conclusion_distribution).map(([k, v]) => (
              <span key={k} style={{ fontSize: 12, color: 'var(--geist-foreground-tertiary)' }}>
                <ConclusionBadge conclusion={k as ReportConclusion} />: {v}
              </span>
            ))}
          </Space>
        </div>
        <Table
          rowKey="run_id"
          dataSource={report.items}
          columns={columns}
          pagination={false}
          size="small"
        />
      </Card>
    </div>
  );
}
