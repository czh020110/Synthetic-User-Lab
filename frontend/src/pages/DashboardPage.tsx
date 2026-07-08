import { Button, Table, message, Typography, Segmented, Space } from 'antd';
import { PlayCircleOutlined, ArrowRightOutlined, RocketOutlined, ReloadOutlined } from '@ant-design/icons';
import { useState } from 'react';
import { useNavigate } from 'react-router';
import { useRuns, useStartDemoRun } from '../hooks/useRuns';
import StatusBadge from '../components/shared/StatusBadge';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

export default function DashboardPage() {
  const navigate = useNavigate();
  const { data: runs, isLoading } = useRuns();
  const startDemo = useStartDemoRun();
  const [filter, setFilter] = useState<'all' | 'running' | 'succeeded' | 'failed'>('all');

  const handleStartDemo = async () => {
    try {
      const result = await startDemo.mutateAsync({ run_name: 'demo' });
      message.success('Demo Run 已启动');
      navigate(`/runs/${result.run_id}?demo=true`);
    } catch (err) {
      message.error(`启动失败: ${(err as Error).message}`);
    }
  };

  const allRuns = runs ?? [];
  const filteredRuns = filter === 'all' ? allRuns : allRuns.filter(r => r.status === filter);

  const stats = {
    total: allRuns.length ?? 0,
    succeeded: (allRuns).filter(r => r.status === 'succeeded').length,
    failed: (allRuns).filter(r => r.status === 'failed').length,
    running: (allRuns).filter(r => r.status === 'running').length,
  };

  const columns = [
    {
      title: 'RUN ID',
      dataIndex: 'run_id',
      key: 'run_id',
      width: 160,
      render: (id: string) => (
        <span
          style={{
            fontFamily: '"SF Mono", "Fira Code", "Cascadia Code", monospace',
            fontSize: 12,
            color: 'var(--geist-foreground-tertiary)',
            cursor: 'pointer',
            fontWeight: 500,
          }}
          onClick={() => navigate(`/runs/${id}`)}
        >
          {id.slice(0, 12)}…
        </span>
      ),
    },
    {
      title: 'STATUS',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => <StatusBadge status={status as any} />,
    },
    {
      title: 'CREATED',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (v: string) => (
        <Text style={{ color: 'var(--geist-foreground-tertiary)', fontSize: 12 }}>
          {dayjs(v).format('YYYY-MM-DD HH:mm')}
        </Text>
      ),
    },
    {
      title: 'ACTIONS',
      key: 'actions',
      width: 180,
      render: (_: any, record: any) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            onClick={() => navigate(`/runs/${record.run_id}`)}
            style={{ fontWeight: 500, padding: 0, fontSize: 12 }}
          >
            Detail
          </Button>
          {(record.status === 'succeeded' || record.status === 'failed') && (
            <Button
              type="link"
              size="small"
              onClick={() => navigate(`/runs/${record.run_id}/report`)}
              style={{ fontWeight: 500, padding: 0, fontSize: 12 }}
            >
              Report
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div className="page-header">
        <Title level={1} className="page-title" style={{ fontSize: 28, fontWeight: 800, letterSpacing: '-0.6px' }}>
          Overview
        </Title>
        <Text className="page-subtitle">
          Synthetic User Lab — Automated UX Testing Platform
        </Text>
      </div>

      {/* Stats */}
      <div className="stats-row">
        <div className="stat-card">
          <Text className="stat-value">{stats.total}</Text>
          <Text className="stat-label">Total Runs</Text>
        </div>
        <div className="stat-card">
          <Text className="stat-value">{stats.succeeded}</Text>
          <Text className="stat-label">Succeeded</Text>
        </div>
        <div className="stat-card">
          <Text className="stat-value">{stats.failed}</Text>
          <Text className="stat-label">Failed</Text>
        </div>
        <div className="stat-card">
          <Text className="stat-value">{stats.running}</Text>
          <Text className="stat-label">Running</Text>
        </div>
      </div>

      {/* Quick Start */}
      <div className="quick-start-card" style={{ marginBottom: 32 }}>
        <div className="quick-start-content">
          <h3>Launch Demo Run</h3>
          <p>
            Start a demo run with preset Persona and Task to experience the full automated testing workflow.
          </p>
        </div>
        <div className="quick-start-action">
          <Button
            type="primary"
            size="large"
            icon={<PlayCircleOutlined />}
            loading={startDemo.isPending}
            onClick={handleStartDemo}
            style={{ height: 36, fontWeight: 600 }}
          >
            Launch Demo Run
          </Button>
        </div>
      </div>

      {/* Quick Actions */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 32, flexWrap: 'wrap' }}>
        <Button
          type="primary"
          icon={<RocketOutlined />}
          onClick={() => navigate('/runs/new')}
          size="large"
          style={{ height: 36, fontWeight: 600 }}
        >
          Start Formal Run
        </Button>
        <Button
          icon={<ReloadOutlined />}
          onClick={() => window.location.reload()}
          size="large"
        >
          Refresh
        </Button>
      </div>

      {/* Recent Runs */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
          <Title level={4} style={{ margin: 0, fontSize: 16, fontWeight: 600, color: 'var(--geist-foreground)' }}>
            Recent Runs
          </Title>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Segmented
              value={filter}
              onChange={(v) => setFilter(v as any)}
              options={[
                { label: 'All', value: 'all' },
                { label: 'Running', value: 'running' },
                { label: 'Succeeded', value: 'succeeded' },
                { label: 'Failed', value: 'failed' },
              ]}
            />
            {allRuns.length > 0 && (
              <Button
                type="link"
                onClick={() => navigate('/entities')}
                style={{ fontWeight: 500, fontSize: 13 }}
              >
                View All <ArrowRightOutlined />
              </Button>
            )}
          </div>
        </div>

        {allRuns.length === 0 && !isLoading ? (
          <div className="empty-state" style={{ padding: 48 }}>
            <div className="empty-icon">🚀</div>
            <h4>No runs yet</h4>
            <p>Launch your first demo run above to get started.</p>
          </div>
        ) : (
          <div className="demo-table">
            <Table
              dataSource={filteredRuns}
              columns={columns}
              rowKey="run_id"
              loading={isLoading}
              pagination={{ pageSize: 10, showSizeChanger: false }}
              size="middle"
              showSorterTooltip={false}
            />
          </div>
        )}
      </div>
    </div>
  );
}
