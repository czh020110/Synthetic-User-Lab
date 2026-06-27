import { Card, Space, Typography, Button, Result, Spin } from 'antd';
import { FileSearchOutlined } from '@ant-design/icons';
import { useNavigate, useParams, useSearchParams } from 'react-router';
import { useRunDetail } from '../hooks/useRunDetail';
import StatusBadge from '../components/shared/StatusBadge';
import StepTimeline from '../components/runs/StepTimeline';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

export default function RunDetailPage() {
  const { runId } = useParams<{ runId: string }>();
  const [searchParams] = useSearchParams();
  const isDemo = searchParams.get('demo') === 'true';
  const navigate = useNavigate();

  const { statusQuery, stepsQuery } = useRunDetail(runId!, isDemo || undefined);

  const status = statusQuery.data;
  const steps = stepsQuery.data;

  if (statusQuery.isLoading) {
    return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  }

  if (!status) {
    return <Result status="404" title="Run Not Found" />;
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Space size="large">
          <Title level={4} style={{ margin: 0 }}>Run Detail</Title>
          <Text>Run ID: {runId?.slice(0, 12)}...</Text>
          <StatusBadge status={status.status} />
          <Text type="secondary">
            {dayjs(status.created_at).format('YYYY-MM-DD HH:mm:ss')}
          </Text>
          {status.status === 'succeeded' || status.status === 'failed' ? (
            <Button
              type="primary"
              icon={<FileSearchOutlined />}
              onClick={() => navigate(`/runs/${runId}/report`)}
            >
              View Report
            </Button>
          ) : null}
        </Space>
      </Card>

      <Card title={`Steps${steps ? ` (${steps.length})` : ''}`}>
        {stepsQuery.isLoading ? (
          <Spin />
        ) : steps && steps.length > 0 ? (
          <StepTimeline steps={steps} />
        ) : (
          <Text type="secondary">
            {status.status === 'queued' ? '等待执行...' : '暂无步骤数据'}
          </Text>
        )}
      </Card>
    </Space>
  );
}
