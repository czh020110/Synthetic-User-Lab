import { Card, Descriptions, Typography, Space } from 'antd';
import ConclusionBadge from '../shared/ConclusionBadge';
import StatusBadge from '../shared/StatusBadge';
import type { RunReport } from '../../types/report';

const { Paragraph, Title, Text } = Typography;

export default function ReportSummary({ report }: { report: RunReport }) {
  return (
    <Card>
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Space size="large">
          <Title level={4} style={{ margin: 0 }}>Report</Title>
          <StatusBadge status={report.status} />
          <ConclusionBadge conclusion={report.conclusion} />
        </Space>

        <Paragraph>{report.summary}</Paragraph>

        <Descriptions bordered size="small" column={2}>
          <Descriptions.Item label="Persona">{report.persona.name}</Descriptions.Item>
          <Descriptions.Item label="Skill Level">{report.persona.skill_level}</Descriptions.Item>
          <Descriptions.Item label="Task">{report.task.name}</Descriptions.Item>
          <Descriptions.Item label="Total Steps">{report.total_steps}</Descriptions.Item>
          <Descriptions.Item label="Success">{report.success ? 'Yes' : 'No'}</Descriptions.Item>
          <Descriptions.Item label="Friction Signals">{report.friction_signals.length}</Descriptions.Item>
        </Descriptions>

        {report.error_message && (
          <Card size="small" type="inner" style={{ background: '#fff2f0' }}>
            <Text type="danger">{report.error_type}: {report.error_message}</Text>
          </Card>
        )}
      </Space>
    </Card>
  );
}
