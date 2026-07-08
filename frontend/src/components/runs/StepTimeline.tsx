import { Card, Timeline, Image, Typography } from 'antd';
import { CheckCircleFilled, CloseCircleFilled, ClockCircleOutlined, LoadingOutlined } from '@ant-design/icons';
import { useState } from 'react';
import type { StepLog } from '../../types/report';
import { screenshotPathToUrl } from '../../api/screenshots';
import dayjs from 'dayjs';

const { Text } = Typography;

export default function StepTimeline({ steps }: { steps: StepLog[] }) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [expandedStep, setExpandedStep] = useState<number | null>(null);

  const items = steps.map((step) => {
    const status = step.validation_result?.status || 'pending';
    let dot;
    if (status === 'succeeded') {
      dot = <CheckCircleFilled style={{ fontSize: 14, color: 'var(--geist-success)' }} />;
    } else if (status === 'running') {
      dot = <LoadingOutlined style={{ fontSize: 14, color: 'var(--geist-foreground)', animation: 'pulse 1.5s infinite' }} />;
    } else if (status === 'failed') {
      dot = <CloseCircleFilled style={{ fontSize: 14, color: 'var(--geist-error)' }} />;
    } else {
      dot = <ClockCircleOutlined style={{ fontSize: 14, color: 'var(--geist-foreground-tertiary)' }} />;
    }

    const screenshotUrl = screenshotPathToUrl(step.observed_page_state?.screenshot_path);
    const actionType = step.decided_action?.action || 'unknown';
    const actionReason = step.decided_action?.reason || '';
    const progressSummary = step.validation_result?.progress_summary || '';
    const isExpanded = expandedStep === step.step_index;

    return {
      dot,
      children: (
        <div
          style={{ cursor: 'pointer', userSelect: 'none' }}
          onClick={() => setExpandedStep(isExpanded ? null : step.step_index)}
        >
          <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--geist-foreground)' }}>
            Step {step.step_index}: {actionType}
          </div>
          {actionReason && (
            <div style={{ fontSize: 12, color: 'var(--geist-foreground-tertiary)', marginTop: 2 }}>
              {actionReason}
            </div>
          )}

          <div style={{
            maxHeight: isExpanded ? 1000 : 0,
            overflow: 'hidden',
            transition: 'max-height 150ms ease',
          }}>
            {progressSummary && (
              <div style={{
                marginTop: 8,
                padding: '8px 12px',
                background: 'var(--geist-code-bg)',
                borderRadius: 4,
                fontSize: 12,
                fontFamily: '"SF Mono", "Fira Code", "Cascadia Code", monospace',
                color: 'var(--geist-foreground-secondary)',
                lineHeight: 1.5,
              }}>
                {progressSummary}
              </div>
            )}
            {step.execution_result?.error_message && (
              <div style={{
                marginTop: 6,
                padding: '8px 12px',
                background: 'var(--geist-overlay)',
                borderRadius: 4,
                fontSize: 12,
                color: 'var(--geist-error)',
                border: '1px solid var(--geist-border)',
              }}>
                {step.execution_result.error_message}
              </div>
            )}
            {screenshotUrl && (
              <img
                src={screenshotUrl}
                alt={`Step ${step.step_index}`}
                style={{
                  marginTop: 8,
                  maxWidth: 200,
                  borderRadius: 4,
                  border: '1px solid var(--geist-border)',
                  cursor: 'pointer',
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  setPreviewUrl(screenshotUrl);
                }}
              />
            )}
            <div style={{ marginTop: 4, fontSize: 11, fontFamily: '"SF Mono", "Fira Code", "Cascadia Code", monospace', color: 'var(--geist-foreground-tertiary)' }}>
              {dayjs(step.before_page_state?.current_url).format('HH:mm:ss')}
            </div>
          </div>

          {!isExpanded && (
            <Text type="secondary" style={{ fontSize: 11, display: 'block', marginTop: 2 }}>
              Click to expand
            </Text>
          )}
        </div>
      ),
    };
  });

  return (
    <Card className="demo-card">
      <Timeline items={items} />
      <Image
        src={previewUrl || ''}
        style={{ display: 'none' }}
        preview={{
          visible: !!previewUrl,
          src: previewUrl || '',
          onVisibleChange: (visible) => { if (!visible) setPreviewUrl(null); },
        }}
      />
    </Card>
  );
}
