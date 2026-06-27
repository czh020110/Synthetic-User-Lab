import { Card, Button, Table, Space, Typography, message } from 'antd';
import { PlayCircleOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router';
import { useRuns, useStartDemoRun } from '../hooks/useRuns';
import StatusBadge from '../components/shared/StatusBadge';
import dayjs from 'dayjs';

const { Title } = Typography;

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

  const columns = [
    {
      title: 'Run ID',
      dataIndex: 'run_id',
      key: 'run_id',
      render: (id: string) => (
        <a onClick={() => navigate(`/runs/${id}`)}>{id.slice(0, 8)}...</a>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => <StatusBadge status={status as any} />,
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (v: string) => dayjs(v).format('MM-DD HH:mm:ss'),
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Space>
          <Title level={4} style={{ margin: 0 }}>Dashboard</Title>
        </Space>
        <div style={{ marginTop: 16 }}>
          <Button
            type="primary"
            size="large"
            icon={<PlayCircleOutlined />}
            loading={startDemo.isPending}
            onClick={handleStartDemo}
          >
            Launch Demo Run
          </Button>
        </div>
      </Card>

      <Card title="Recent Runs">
        <Table
          dataSource={recentRuns}
          columns={columns}
          rowKey="run_id"
          loading={isLoading}
          pagination={false}
          size="small"
        />
      </Card>
    </Space>
  );
}
