import { Card, List, Typography } from 'antd';

const { Title } = Typography;

export default function Recommendations({ recommendations }: { recommendations: string[] }) {
  if (!recommendations.length) return null;

  return (
    <Card title={<Title level={5} style={{ margin: 0 }}>Recommendations</Title>}>
      <List
        size="small"
        dataSource={recommendations}
        renderItem={(item) => <List.Item>{item}</List.Item>}
      />
    </Card>
  );
}
