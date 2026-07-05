import { Card, Descriptions, Typography, Space } from 'antd';
import ConclusionBadge from '../shared/ConclusionBadge';
import StatusBadge from '../shared/StatusBadge';
import type { RunReport } from '../../types/report';

const { Paragraph, Title, Text } = Typography;

export default function ReportSummary({ report }: { report: RunReport }) {
  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Space size="middle" align="center">
          <Title level={2} style={{ margin: 0 }}>Report</Title>
          <StatusBadge status={report.status} />
          <ConclusionBadge conclusion={report.conclusion} />
        </Space>
      </div>

      <Card style={{ marginBottom: 16 }}>
        <Paragraph style={{ fontSize: 15, lineHeight: 1.8 }}>
          {report.summary}
        </Paragraph>
      </Card>

      <Card style={{ marginBottom: 24 }}>
        <Descriptions bordered size="small" column={3}>
          <Descriptions.Item label="Persona">{report.persona?.name || '—'}</Descriptions.Item>
          <Descriptions.Item label="Skill Level">{report.persona?.skill_level || '—'}</Descriptions.Item>
          <Descriptions.Item label="Task">{report.task?.name || '—'}</Descriptions.Item>
          <Descriptions.Item label="Total Steps">{report.total_steps}</Descriptions.Item>
          <Descriptions.Item label="Success">{report.success ? 'Yes' : 'No'}</Descriptions.Item>
          <Descriptions.Item label="Friction Signals">{report.friction_signals.length}</Descriptions.Item>
        </Descriptions>

        {report.error_message && (
          <Card
            size="small"
            style={{
              background: '#fff2f0',
              border: '1px solid #ffccc7',
              marginTop: 16,
            }}
          >
            <Text type="danger" style={{ fontWeight: 500 }}>
              {report.error_type}: {report.error_message}
            </Text>
          </Card>
        )}
      </Card>
    </div>
  );
}
