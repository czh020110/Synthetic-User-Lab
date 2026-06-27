import { Timeline, Card, Tag, Image, Typography, Space } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, SyncOutlined, ClockCircleOutlined } from '@ant-design/icons';
import type { StepLog } from '../../types/report';
import { screenshotPathToUrl } from '../../api/screenshots';

const { Text, Paragraph } = Typography;

export default function StepTimeline({ steps }: { steps: StepLog[] }) {
  return (
    <Timeline
      items={steps.map((step) => {
        const isSuccess = step.execution_result.success;
        const icon = isSuccess
          ? <CheckCircleOutlined style={{ color: '#52c41a' }} />
          : <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;

        const beforeUrl = screenshotPathToUrl(step.observed_page_state.screenshot_path);
        const afterUrl = screenshotPathToUrl(step.post_action_page_state.screenshot_path);

        return {
          dot: icon,
          children: (
            <Card size="small" style={{ marginBottom: 8 }}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Space>
                  <Tag color="blue">Step {step.step_index}</Tag>
                  <Tag>{step.decided_action.action}</Tag>
                  {step.decided_action.reason && (
                    <Text type="secondary">{step.decided_action.reason}</Text>
                  )}
                </Space>

                <Paragraph ellipsis={{ rows: 2 }}>
                  {step.execution_result.detail}
                </Paragraph>

                <Space>
                  {beforeUrl && (
                    <div>
                      <Text type="secondary" style={{ fontSize: 12 }}>Before:</Text>
                      <Image src={beforeUrl} width={160} style={{ display: 'block', marginTop: 4 }} />
                    </div>
                  )}
                  {afterUrl && (
                    <div>
                      <Text type="secondary" style={{ fontSize: 12 }}>After:</Text>
                      <Image src={afterUrl} width={160} style={{ display: 'block', marginTop: 4 }} />
                    </div>
                  )}
                </Space>

                {step.validation_result.friction_signals.length > 0 && (
                  <Space>
                    <Text type="warning" style={{ fontSize: 12 }}>Friction:</Text>
                    {step.validation_result.friction_signals.map((s, i) => (
                      <Tag key={i} color="warning" style={{ fontSize: 11 }}>{s}</Tag>
                    ))}
                  </Space>
                )}
              </Space>
            </Card>
          ),
        };
      })}
    />
  );
}
