import { Spin, Result, Button, Typography } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate, useParams, useSearchParams } from 'react-router';
import { useRunDetail } from '../hooks/useRunDetail';
import ReportSummary from '../components/report/ReportSummary';
import KeyFindings from '../components/report/KeyFindings';
import FrictionIssues from '../components/report/FrictionIssues';
import KeyScreenshots from '../components/report/KeyScreenshots';
import Recommendations from '../components/report/Recommendations';

const { Title } = Typography;

export default function ReportPage() {
  const { runId } = useParams<{ runId: string }>();
  const [searchParams] = useSearchParams();
  const isDemo = searchParams.get('demo') === 'true';
  const navigate = useNavigate();

  const { reportQuery } = useRunDetail(runId!, isDemo || undefined);
  const report = reportQuery.data;

  if (reportQuery.isLoading) {
    return (
      <div className="loading-container">
        <Spin size="large" />
      </div>
    );
  }

  if (reportQuery.error) {
    return (
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate(`/runs/${runId}`)}
            style={{ borderRadius: 8 }}
          />
          <Title level={1} style={{ margin: 0, fontSize: 24, fontWeight: 700, color: 'var(--color-text-primary)' }}>
            Report
          </Title>
        </div>
        <Result
          status="warning"
          title="Report Not Available"
          subTitle={(reportQuery.error as Error).message}
        />
      </div>
    );
  }

  if (!report) {
    return (
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate(`/runs/${runId}`)}
            style={{ borderRadius: 8 }}
          />
          <Title level={1} style={{ margin: 0, fontSize: 24, fontWeight: 700, color: 'var(--color-text-primary)' }}>
            Report
          </Title>
        </div>
        <Result status="404" title="Report Not Found" />
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate(`/runs/${runId}`)}
          style={{ borderRadius: 8 }}
        />
        <Title level={1} style={{ margin: 0, fontSize: 24, fontWeight: 700, color: 'var(--color-text-primary)' }}>
          Report
        </Title>
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
