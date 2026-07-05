import { Typography, Alert, Empty } from 'antd';
import type { FrictionIssue } from '../../types/report';

const { Text } = Typography;

export default function FrictionIssues({ issues }: { issues: FrictionIssue[] }) {
  if (!issues || issues.length === 0) {
    return (
      <Empty
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        description={<span style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>No friction signals detected</span>}
        style={{ padding: '16px 0' }}
      />
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {issues.map((issue, index) => (
        <Alert
          key={`${issue.signal}-${index}`}
          message={
            <div>
              <Text strong style={{ fontSize: 13 }}>{issue.signal}</Text>
              {issue.description && (
                <Text style={{ display: 'block', marginTop: 4, fontSize: 13, color: 'var(--color-text-secondary)' }}>
                  {issue.description}
                </Text>
              )}
              {issue.suggested_fix && (
                <Text style={{ display: 'block', marginTop: 4, fontSize: 12, color: 'var(--color-text-muted)' }}>
                  Fix: {issue.suggested_fix}
                </Text>
              )}
            </div>
          }
          type="warning"
          showIcon
          style={{ borderRadius: 6 }}
        />
      ))}
    </div>
  );
}
