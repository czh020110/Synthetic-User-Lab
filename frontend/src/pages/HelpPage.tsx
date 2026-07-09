import { Typography, Card, Collapse, List, Space, Button, Steps } from 'antd';
import { ArrowLeftOutlined, RocketOutlined, PlayCircleOutlined, FileSearchOutlined, TeamOutlined, QuestionCircleOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router';

const { Title, Text, Paragraph } = Typography;

export default function HelpPage() {
  const navigate = useNavigate();

  const quickStartSteps = [
    {
      title: 'Create Entities',
      description: 'Navigate to the Entities page to create Personas, Tasks, and Knowledge items.',
    },
    {
      title: 'Start a Run',
      description: 'Use the "Start Run" button to launch a run with one or more Personas and a Task.',
    },
    {
      title: 'Monitor Progress',
      description: 'View real-time step logs and screenshots in the Run Detail page.',
    },
    {
      title: 'Review Report',
      description: 'After completion, view the comprehensive report with findings and recommendations.',
    },
  ];

  const faqItems = [
    {
      key: '1',
      label: 'What is a Persona?',
      children: (
        <Paragraph>
          A Persona represents a synthetic user profile with specific skill level, patience, and risk preference.
          Personas are used to simulate different types of users during automated testing.
        </Paragraph>
      ),
    },
    {
      key: '2',
      label: 'What is a Task?',
      children: (
        <Paragraph>
          A Task defines a specific testing scenario with a start URL, success criteria, max steps, and allowed actions.
          Tasks are executed by AI agents guided by a Persona.
        </Paragraph>
      ),
    },
    {
      key: '3',
      label: 'What is a Knowledge Item?',
      children: (
        <Paragraph>
          Knowledge Items provide context for RAG (Retrieval-Augmented Generation) during run execution.
          They include Product Knowledge and Failure Cases to help the AI agent make better decisions.
        </Paragraph>
      ),
    },
    {
      key: '4',
      label: 'Can I compare multiple Personas on the same Task?',
      children: (
        <Paragraph>
          Yes. On the Start Run page, select multiple Personas to launch a batch run. Once all runs finish,
          a cross-persona comparison report highlights differences in success rate, conclusion, step count and friction signals.
        </Paragraph>
      ),
    },
    {
      key: '5',
      label: 'How does the security guard work?',
      children: (
        <Paragraph>
          The security guard automatically blocks high-risk actions (payment, deletion, publishing) in production environments.
          You can enable destructive actions per Task, but this is not recommended for production testing.
        </Paragraph>
      ),
    },
    {
      key: '6',
      label: 'How are screenshots captured?',
      children: (
        <Paragraph>
          Screenshots are automatically captured at key points: before actions, after actions, and during wait observations.
          They are stored locally and can be viewed in the Run Detail and Report pages.
        </Paragraph>
      ),
    },
  ];

  const keyFeatures = [
    { icon: <TeamOutlined />, title: 'Entity Management', description: 'Create and manage Personas, Tasks, and Knowledge items' },
    { icon: <RocketOutlined />, title: 'Start Run', description: 'Launch a run with custom Persona(s) and Task' },
    { icon: <PlayCircleOutlined />, title: 'Multi-Persona Compare', description: 'Batch run and cross-persona friction comparison' },
    { icon: <FileSearchOutlined />, title: 'Detailed Reports', description: 'Comprehensive reports with findings and recommendations' },
  ];

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/')}
        />
        <Title level={1} className="page-title">
          Help & Documentation
        </Title>
      </div>

      <Card className="demo-card" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
          <QuestionCircleOutlined style={{ fontSize: 40, color: 'var(--geist-foreground-tertiary)' }} />
          <div>
            <Title level={3} style={{ marginTop: 0 }}>Welcome to Synthetic User Lab</Title>
            <Paragraph style={{ fontSize: 14, lineHeight: 1.6 }}>
              Synthetic User Lab is an automated UX testing platform that uses AI agents to simulate user behavior.
              It helps you identify usability issues, friction points, and areas for improvement in your web applications.
            </Paragraph>
          </div>
        </div>
      </Card>

      <Card className="demo-card" style={{ marginBottom: 24 }}>
        <Title level={4}>Key Features</Title>
        <List
          grid={{ gutter: 24, xs: 1, sm: 2 }}
          dataSource={keyFeatures}
          renderItem={(item) => (
            <List.Item>
              <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                <div style={{ fontSize: 20, color: 'var(--geist-foreground-tertiary)' }}>{item.icon}</div>
                <div>
                  <Text strong style={{ display: 'block', marginBottom: 4 }}>{item.title}</Text>
                  <Text type="secondary" style={{ fontSize: 13 }}>{item.description}</Text>
                </div>
              </div>
            </List.Item>
          )}
        />
      </Card>

      <Card className="demo-card" style={{ marginBottom: 24 }}>
        <Title level={4}>Quick Start Guide</Title>
        <Steps
          direction="vertical"
          current={-1}
          items={quickStartSteps}
        />
      </Card>

      <Card className="demo-card">
        <Title level={4}>Frequently Asked Questions</Title>
        <Collapse items={faqItems} />
      </Card>

      <div style={{ marginTop: 24, textAlign: 'center' }}>
        <Space direction="vertical" size="small">
          <Text type="secondary">Need more help?</Text>
          <Button type="link" onClick={() => navigate('/settings')}>Contact Support</Button>
        </Space>
      </div>
    </div>
  );
}
