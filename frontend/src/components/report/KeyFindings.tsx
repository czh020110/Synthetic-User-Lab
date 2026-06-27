import { Card, List, Typography } from 'antd';

const { Title } = Typography;

export default function KeyFindings({ findings }: { findings: string[] }) {
  if (!findings.length) return null;

  return (
    <Card title={<Title level={5} style={{ margin: 0 }}>Key Findings</Title>}>
      <List
        size="small"
        dataSource={findings}
        renderItem={(item) => <List.Item>{item}</List.Item>}
      />
    </Card>
  );
}
