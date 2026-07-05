import { Card, Timeline, Image } from 'antd';
import { CheckCircleFilled, CloseCircleFilled, ClockCircleOutlined, LoadingOutlined } from '@ant-design/icons';
import { useState } from 'react';
import type { StepLog } from '../../types/report';
import { screenshotPathToUrl } from '../../api/screenshots';
import dayjs from 'dayjs';

export default function StepTimeline({ steps }: { steps: StepLog[] }) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const items = steps.map((step) => {
    const status = step.validation_result?.status || 'pending';
    let dot;
    if (status === 'succeeded') {
      dot = <CheckCircleFilled style={{ fontSize: 16, color: 'var(--color-success)' }} />;
    } else if (status === 'running') {
      dot = <LoadingOutlined style={{ fontSize: 16, color: 'var(--color-primary)', animation: 'pulse 1.5s infinite' }} />;
    } else if (status === 'failed') {
      dot = <CloseCircleFilled style={{ fontSize: 16, color: 'var(--color-error)' }} />;
    } else {
      dot = <ClockCircleOutlined style={{ fontSize: 16, color: 'var(--color-text-muted)' }} />;
    }

    const screenshotUrl = screenshotPathToUrl(step.observed_page_state?.screenshot_path);
    const actionType = step.decided_action?.action || 'unknown';
    const actionReason = step.decided_action?.reason || '';
    const progressSummary = step.validation_result?.progress_summary || '';

    return {
      dot,
      children: (
        <div>
          <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--color-text-primary)' }}>
            Step {step.step_index}: {actionType}
          </div>
          {actionReason && (
            <div style={{ fontSize: 13, color: 'var(--color-text-muted)', marginTop: 2 }}>
              {actionReason}
            </div>
          )}
          {progressSummary && (
            <div style={{
              marginTop: 6,
              padding: '6px 10px',
              background: 'var(--color-bg)',
              borderRadius: 4,
              fontSize: 12,
              color: 'var(--color-text-secondary)',
            }}>
              {progressSummary}
            </div>
          )}
          {step.execution_result?.error_message && (
            <div style={{
              marginTop: 4,
              padding: '6px 10px',
              background: '#fff2f0',
              borderRadius: 4,
              fontSize: 12,
              color: 'var(--color-error)',
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
                maxWidth: '200px',
                borderRadius: 6,
                border: '1px solid var(--color-border)',
                cursor: 'pointer',
              }}
              onClick={() => setPreviewUrl(screenshotUrl)}
            />
          )}
          <div style={{ marginTop: 4, fontSize: 11, color: 'var(--color-text-muted)' }}>
            {dayjs(step.before_page_state?.current_url).format('HH:mm:ss')}
          </div>
        </div>
      ),
    };
  });

  return (
    <Card>
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
