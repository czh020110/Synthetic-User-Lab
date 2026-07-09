import { Button, Typography, Breadcrumb, Space } from 'antd';
import { ArrowLeftOutlined, DownloadOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router';
import { useRunDetail } from '../hooks/useRunDetail';
import { useRunReportMarkdown } from '../hooks/useRunReportMarkdown';
import ReportSummary from '../components/report/ReportSummary';
import KeyFindings from '../components/report/KeyFindings';
import FrictionIssues from '../components/report/FrictionIssues';
import KeyScreenshots from '../components/report/KeyScreenshots';
import Recommendations from '../components/report/Recommendations';
import { AppEmpty, AppErrorState, AppLoading } from '../components/feedback/AppFeedback';
import { getErrorMessage } from '../lib/api-error';

const { Title } = Typography;

export default function ReportPage() {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();

  const { reportQuery } = useRunDetail(runId!);
  const { data: markdownReport } = useRunReportMarkdown(runId!);
  const report = reportQuery.data;

  const displayId = runId && runId.length > 12 ? `${runId.slice(0, 12)}…` : runId || '';

  const handleDownloadMarkdown = () => {
    if (!markdownReport?.markdown) return;
    const blob = new Blob([markdownReport.markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `report-${runId}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (reportQuery.isLoading) {
    return <AppLoading tip="加载报告…" minHeight={280} />;
  }

  if (reportQuery.isError) {
    return (
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate(`/runs/${runId}`)}
          />
          <Title level={1} className="page-title">
            Report
          </Title>
        </div>
        <AppErrorState
          title="Report Not Available"
          description={getErrorMessage(reportQuery.error, '请稍后重试')}
          onRetry={() => reportQuery.refetch()}
        />
      </div>
    );
  }

  if (!report) {
    return (
      <AppEmpty
        title="Report Not Found"
        description="当前运行还没有可展示的报告。"
        action={
          <Button type="primary" onClick={() => navigate(`/runs/${runId}`)}>
            Back to Run Detail
          </Button>
        }
      />
    );
  }

  return (
    <div>
      {/* Breadcrumb */}
      <Breadcrumb
        style={{ marginBottom: 16 }}
        items={[
          { title: <span style={{ cursor: 'pointer' }} onClick={() => navigate('/')}>Dashboard</span> },
          { title: <span style={{ cursor: 'pointer' }} onClick={() => navigate(`/runs/${runId}`)}>Run {displayId}</span> },
          { title: 'Report' },
        ]}
      />

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate(`/runs/${runId}`)}
          />
          <Title level={1} className="page-title">
            Report
          </Title>
        </div>
        <Space>
          {markdownReport?.markdown && (
            <Button
              icon={<DownloadOutlined />}
              onClick={handleDownloadMarkdown}
            >
              Download Markdown
            </Button>
          )}
        </Space>
      </div>

      <ReportSummary report={report} />
      <div className="section-spacer" />

      <div className="report-section">
        <h2 className="report-section-title">Key Findings</h2>
        <KeyFindings findings={report.key_findings} />
      </div>

      <div className="report-section">
        <h2 className="report-section-title">Friction Issues</h2>
        <FrictionIssues issues={report.friction_issues} />
      </div>

      <div className="report-section">
        <h2 className="report-section-title">Key Screenshots</h2>
        <KeyScreenshots screenshots={report.key_screenshots} />
      </div>

      <div className="report-section">
        <h2 className="report-section-title">Recommendations</h2>
        <Recommendations recommendations={report.next_recommendations} />
      </div>
    </div>
  );
}
