import { List, Typography } from 'antd';

const { Text } = Typography;

export default function Recommendations({ recommendations }: { recommendations: string[] }) {
  if (!recommendations || recommendations.length === 0) return null;

  return (
    <List
      size="small"
      dataSource={recommendations}
      renderItem={(item) => (
        <div className="finding-item">
          <Text>💡 {item}</Text>
        </div>
      )}
    />
  );
}
