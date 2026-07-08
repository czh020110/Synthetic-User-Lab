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
          <Title level={2} style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Report</Title>
          <StatusBadge status={report.status} />
          <ConclusionBadge conclusion={report.conclusion} />
        </Space>
      </div>

      <Card className="demo-card" style={{ marginBottom: 12 }}>
        <Paragraph style={{ fontSize: 14, lineHeight: 1.7 }}>
          {report.summary}
        </Paragraph>
      </Card>

      <Card className="demo-card" style={{ marginBottom: 24 }}>
        <Descriptions bordered size="small" column={3}>
          <Descriptions.Item label="Persona">{report.persona?.name || '—'}</Descriptions.Item>
          <Descriptions.Item label="Skill Level">{report.persona?.skill_level || '—'}</Descriptions.Item>
          <Descriptions.Item label="Task">{report.task?.name || '—'}</Descriptions.Item>
          <Descriptions.Item label="Total Steps">{report.total_steps}</Descriptions.Item>
          <Descriptions.Item label="Success">{report.success ? 'Yes' : 'No'}</Descriptions.Item>
          <Descriptions.Item label="Friction Signals">{report.friction_signals.length}</Descriptions.Item>
        </Descriptions>

        {report.error_message && (
          <div style={{
            marginTop: 16,
            padding: '12px 16px',
            background: 'var(--geist-overlay)',
            borderRadius: 5,
            border: '1px solid var(--geist-border)',
          }}>
            <Text type="danger" style={{ fontWeight: 500, fontSize: 13 }}>
              {report.error_type}: {report.error_message}
            </Text>
          </div>
        )}
      </Card>
    </div>
  );
}
