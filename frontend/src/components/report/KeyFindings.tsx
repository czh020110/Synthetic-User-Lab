import { List, Typography } from 'antd';

const { Text } = Typography;

export default function KeyFindings({ findings }: { findings: string[] }) {
  if (!findings || findings.length === 0) return null;

  return (
    <List
      size="small"
      dataSource={findings}
      renderItem={(item) => (
        <div className="finding-item">
          <Text>• {item}</Text>
        </div>
      )}
    />
  );
}
