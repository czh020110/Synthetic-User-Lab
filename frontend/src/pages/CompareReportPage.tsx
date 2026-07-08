import { Card, Table, Tag, Button, Typography, Statistic, Row, Col, Progress, Space } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate, useSearchParams } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import * as api from '../api/runs';
import { conclusionConfig } from '../components/shared/badgeConfig';
import type { RunStatusResponse } from '../types/run';
import type { CompareItem, CompareReport, ReportConclusion } from '../types/report';
import { AppEmpty, AppErrorState, AppLoading } from '../components/feedback/AppFeedback';
import { getErrorMessage } from '../lib/api-error';

const { Title, Text } = Typography;

function isTerminal(status?: string) {
  return status === 'succeeded' || status === 'failed';
}

// 对比报告的 400/404/409 是永久错误，重试不会成功；仅对网络等瞬时错误重试一次
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

  // 单请求拉取全部 run 状态再按 runIds 过滤，避免每轮 N 次 GET /runs/{id}
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

  // polling 失败或存在缺失 run：显式报错，避免无限 spinner
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
          <Title level={1} style={{ margin: 0, fontSize: 24, fontWeight: 700 }}>{t('compare.title')}</Title>
        </div>
        <Card>
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
      render: (c: ReportConclusion) => {
        const cfg = conclusionConfig[c] ?? { color: 'default', labelKey: c };
        return <Tag color={cfg.color}>{t(cfg.labelKey)}</Tag>;
      },
    },
    {
      title: t('compare.columns.result'),
      dataIndex: 'success',
      render: (s: boolean) => (s ? <Tag color="success">{t('compare.resultSuccess')}</Tag> : <Tag color="error">{t('compare.resultFailed')}</Tag>),
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
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/')} style={{ borderRadius: 8 }} />
        <Title level={1} style={{ margin: 0, fontSize: 24, fontWeight: 700, color: 'var(--color-text-primary)' }}>
          {t('compare.title')}
        </Title>
      </div>
      <Text style={{ fontSize: 14, color: 'var(--color-text-muted)', display: 'block', marginBottom: 24 }}>
        任务：{report.task.name} · {report.comparison_summary}
      </Text>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card><Statistic title={t('compare.participants')} value={report.run_count} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title={t('compare.success')} value={report.success_count} suffix={`/ ${report.run_count}`} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title={t('compare.avgSteps')} value={report.avg_steps} precision={1} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title={t('compare.totalFriction')} value={report.total_friction_signals} /></Card>
        </Col>
      </Row>

      <Card style={{ borderRadius: 12, border: '1px solid var(--color-border)' }}>
        <div style={{ marginBottom: 12 }}>
          <Text strong>{t('compare.distribution')}</Text>
          <Space style={{ marginLeft: 12 }}>
            {Object.entries(report.conclusion_distribution).map(([k, v]) => {
              const cfg = conclusionConfig[k as ReportConclusion] ?? { color: 'default', labelKey: k };
              return (
                <Tag key={k} color={cfg.color}>
                  {t(cfg.labelKey)}: {v}
                </Tag>
              );
            })}
          </Space>
        </div>
        <Table
          rowKey="run_id"
          dataSource={report.items}
          columns={columns}
          pagination={false}
          size="middle"
        />
      </Card>
    </div>
  );
}
