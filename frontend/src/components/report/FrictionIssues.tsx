import { Card, Table, Tag, Typography } from 'antd';
import type { FrictionIssue, FrictionSeverity } from '../../types/report';

const { Title } = Typography;

const severityColor: Record<FrictionSeverity, string> = {
  low: 'green',
  medium: 'orange',
  high: 'red',
};

export default function FrictionIssues({ issues }: { issues: FrictionIssue[] }) {
  if (!issues.length) return null;

  const columns = [
    { title: 'Signal', dataIndex: 'signal', key: 'signal' },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      render: (s: FrictionSeverity) => <Tag color={severityColor[s]}>{s}</Tag>,
    },
    { title: 'Steps', dataIndex: 'step_indexes', key: 'step_indexes', render: (v: number[]) => v.join(', ') },
    { title: 'Description', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: 'Suggested Fix', dataIndex: 'suggested_fix', key: 'suggested_fix', ellipsis: true },
  ];

  return (
    <Card title={<Title level={5} style={{ margin: 0 }}>Friction Issues</Title>}>
      <Table
        dataSource={issues}
        columns={columns}
        rowKey={(_, i) => String(i)}
        size="small"
        pagination={false}
      />
    </Card>
  );
}
