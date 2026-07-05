import { Card, Button, Table, message, Typography } from 'antd';
import { PlayCircleOutlined, ArrowRightOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router';
import { useRuns, useStartDemoRun } from '../hooks/useRuns';
import StatusBadge from '../components/shared/StatusBadge';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

export default function DashboardPage() {
  const navigate = useNavigate();
  const { data: runs, isLoading } = useRuns();
  const startDemo = useStartDemoRun();

  const handleStartDemo = async () => {
    try {
      const result = await startDemo.mutateAsync({ run_name: 'demo' });
      message.success('Demo Run 已启动');
      navigate(`/runs/${result.run_id}?demo=true`);
    } catch (err) {
      message.error(`启动失败: ${(err as Error).message}`);
    }
  };

  const recentRuns = (runs || []).slice(0, 10);

  const stats = {
    total: runs?.length ?? 0,
    succeeded: (runs || []).filter(r => r.status === 'succeeded').length,
    failed: (runs || []).filter(r => r.status === 'failed').length,
    running: (runs || []).filter(r => r.status === 'running').length,
  };

  const columns = [
    {
      title: 'Run ID',
      dataIndex: 'run_id',
      key: 'run_id',
      width: 160,
      render: (id: string) => (
        <span
          style={{
            fontFamily: 'SFMono-Regular, Consolas, monospace',
            fontSize: 13,
            color: 'var(--color-primary)',
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
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => <StatusBadge status={status as any} />,
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (v: string) => (
        <Text style={{ color: 'var(--color-text-muted)', fontSize: 13 }}>
          {dayjs(v).format('YYYY-MM-DD HH:mm')}
        </Text>
      ),
    },
  ];

  return (
    <div>
      <div className="page-header">
        <Title level={1} className="page-title" style={{ fontSize: 28, fontWeight: 700 }}>
          Dashboard
        </Title>
        <Text className="page-subtitle">
          Synthetic User Lab — 自动化用户体验测试平台
        </Text>
      </div>

      {/* Stats */}
      <div className="stats-row">
        <Card className="stat-card" bordered={false} style={{ borderRadius: 12 }}>
          <Text style={{ fontSize: 32, fontWeight: 700, color: 'var(--color-text-primary)', display: 'block', lineHeight: 1.2 }}>
            {stats.total}
          </Text>
          <Text style={{ fontSize: 13, color: 'var(--color-text-muted)', fontWeight: 500 }}>Total Runs</Text>
        </Card>
        <Card className="stat-card" bordered={false} style={{ borderRadius: 12 }}>
          <Text style={{ fontSize: 32, fontWeight: 700, color: 'var(--color-success)', display: 'block', lineHeight: 1.2 }}>
            {stats.succeeded}
          </Text>
          <Text style={{ fontSize: 13, color: 'var(--color-text-muted)', fontWeight: 500 }}>Succeeded</Text>
        </Card>
        <Card className="stat-card" bordered={false} style={{ borderRadius: 12 }}>
          <Text style={{ fontSize: 32, fontWeight: 700, color: 'var(--color-error)', display: 'block', lineHeight: 1.2 }}>
            {stats.failed}
          </Text>
          <Text style={{ fontSize: 13, color: 'var(--color-text-muted)', fontWeight: 500 }}>Failed</Text>
        </Card>
        <Card className="stat-card" bordered={false} style={{ borderRadius: 12 }}>
          <Text style={{ fontSize: 32, fontWeight: 700, color: 'var(--color-primary)', display: 'block', lineHeight: 1.2 }}>
            {stats.running}
          </Text>
          <Text style={{ fontSize: 13, color: 'var(--color-text-muted)', fontWeight: 500 }}>Running</Text>
        </Card>
      </div>

      {/* Quick Start */}
      <div className="quick-start-card" style={{ marginBottom: 28 }}>
        <div className="quick-start-content">
          <h3 style={{ margin: '0 0 8px 0', fontSize: 18, fontWeight: 600, color: 'var(--color-text-primary)' }}>
            Launch Demo Run
          </h3>
          <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: 14, lineHeight: 1.6 }}>
            启动一个演示运行，使用预设的 Persona 和 Task
            <br />
            快速体验完整的自动化测试流程。
          </p>
        </div>
        <div className="quick-start-action">
          <Button
            type="primary"
            size="large"
            icon={<PlayCircleOutlined />}
            loading={startDemo.isPending}
            onClick={handleStartDemo}
            className="btn-primary-gradient"
          >
            Launch Demo Run
          </Button>
        </div>
      </div>

      {/* Recent Runs */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <Title level={4} style={{ margin: 0, fontSize: 16, fontWeight: 600, color: 'var(--color-text-primary)' }}>
            Recent Runs
          </Title>
          {recentRuns.length > 0 && (
            <Button
              type="link"
              onClick={() => navigate('/entities')}
              style={{ fontWeight: 500, fontSize: 13 }}
            >
              View All <ArrowRightOutlined />
            </Button>
          )}
        </div>

        {recentRuns.length === 0 && !isLoading ? (
          <div className="empty-state" style={{ padding: 48 }}>
            <div className="empty-icon" style={{ fontSize: 40, marginBottom: 12 }}>🚀</div>
            <h4 style={{ margin: '0 0 8px 0', fontSize: 15, fontWeight: 600, color: 'var(--color-text-primary)' }}>
              No runs yet
            </h4>
            <p style={{ margin: '0 0 16px 0', color: 'var(--color-text-muted)', fontSize: 14 }}>
              Launch your first demo run above to get started.
            </p>
          </div>
        ) : (
          <div className="demo-table">
            <Table
              dataSource={recentRuns}
              columns={columns}
              rowKey="run_id"
              loading={isLoading}
              pagination={false}
              size="middle"
              showSorterTooltip={false}
            />
          </div>
        )}
      </div>
    </div>
  );
}
