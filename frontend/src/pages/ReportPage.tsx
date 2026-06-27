import { Space, Spin, Result, Button } from 'antd';
import { useNavigate, useParams, useSearchParams } from 'react-router';
import { useRunDetail } from '../hooks/useRunDetail';
import ReportSummary from '../components/report/ReportSummary';
import KeyFindings from '../components/report/KeyFindings';
import FrictionIssues from '../components/report/FrictionIssues';
import KeyScreenshots from '../components/report/KeyScreenshots';
import Recommendations from '../components/report/Recommendations';

export default function ReportPage() {
  const { runId } = useParams<{ runId: string }>();
  const [searchParams] = useSearchParams();
  const isDemo = searchParams.get('demo') === 'true';
  const navigate = useNavigate();

  const { reportQuery } = useRunDetail(runId!, isDemo || undefined);
  const report = reportQuery.data;

  if (reportQuery.isLoading) {
    return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  }

  if (reportQuery.error) {
    return (
      <Result
        status="warning"
        title="Report Not Available"
        subTitle={(reportQuery.error as Error).message}
        extra={
          <Button onClick={() => navigate(`/runs/${runId}`)}>
            Back to Run Detail
          </Button>
        }
      />
    );
  }

  if (!report) {
    return <Result status="404" title="Report Not Found" />;
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <ReportSummary report={report} />
      <KeyFindings findings={report.key_findings} />
      <FrictionIssues issues={report.friction_issues} />
      <KeyScreenshots screenshots={report.key_screenshots} />
      <Recommendations recommendations={report.next_recommendations} />
    </Space>
  );
}
