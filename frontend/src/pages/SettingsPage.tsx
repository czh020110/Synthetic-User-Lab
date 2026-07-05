import { Typography, Card, Divider, Switch, Select, Input, Button, Space, message, Form, Alert } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useState } from 'react';
import { useNavigate } from 'react-router';

const { Title, Text, Paragraph } = Typography;

export default function SettingsPage() {
  const navigate = useNavigate();
  const [generalForm] = Form.useForm();
  const [runForm] = Form.useForm();
  const [notifForm] = Form.useForm();
  const [saved, setSaved] = useState(false);

  const emailNotifications = Form.useWatch('emailNotifications', notifForm);

  const handleSave = async () => {
    try {
      await Promise.all([
        generalForm.validateFields(),
        runForm.validateFields(),
        notifForm.validateFields(),
      ]);
      setSaved(true);
      message.success('Settings saved successfully');
      setTimeout(() => setSaved(false), 3000);
    } catch {
      message.error('Please check the form fields');
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/')}
          style={{ borderRadius: 8 }}
        />
        <Title level={1} style={{ margin: 0, fontSize: 24, fontWeight: 700, color: 'var(--color-text-primary)' }}>
          Settings
        </Title>
      </div>

      {saved && (
        <Alert
          message="Settings saved"
          type="success"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <Card className="demo-card" style={{ borderRadius: 12, border: '1px solid var(--color-border)' }}>
          <Title level={4} style={{ marginBottom: 16 }}>General Settings</Title>
          <Form form={generalForm} layout="vertical" initialValues={{
            language: 'en',
            timezone: 'UTC',
            dateFormat: 'YYYY-MM-DD',
            theme: 'light',
          }}>
            <Form.Item name="language" label="Language">
              <Select
                options={[
                  { value: 'en', label: 'English' },
                  { value: 'zh', label: '中文' },
                ]}
              />
            </Form.Item>
            <Form.Item name="timezone" label="Timezone">
              <Select
                options={[
                  { value: 'UTC', label: 'UTC' },
                  { value: 'Asia/Shanghai', label: 'Asia/Shanghai' },
                  { value: 'America/New_York', label: 'America/New_York' },
                ]}
              />
            </Form.Item>
            <Form.Item name="dateFormat" label="Date Format">
              <Select
                options={[
                  { value: 'YYYY-MM-DD', label: 'YYYY-MM-DD' },
                  { value: 'DD/MM/YYYY', label: 'DD/MM/YYYY' },
                  { value: 'MM/DD/YYYY', label: 'MM/DD/YYYY' },
                ]}
              />
            </Form.Item>
            <Form.Item name="theme" label="Theme">
              <Select
                options={[
                  { value: 'light', label: 'Light' },
                  { value: 'dark', label: 'Dark' },
                  { value: 'auto', label: 'Auto' },
                ]}
              />
            </Form.Item>
          </Form>
        </Card>

        <Card className="demo-card" style={{ borderRadius: 12, border: '1px solid var(--color-border)' }}>
          <Title level={4} style={{ marginBottom: 16 }}>Run Settings</Title>
          <Form form={runForm} layout="vertical" initialValues={{
            defaultHeadless: true,
            defaultMaxSteps: 30,
            autoRefresh: true,
            refreshInterval: 5000,
          }}>
            <Form.Item name="defaultHeadless" label="Default Headless Mode" valuePropName="checked">
              <Switch />
            </Form.Item>
            <Form.Item name="autoRefresh" label="Auto Refresh Run Status" valuePropName="checked">
              <Switch />
            </Form.Item>
            <Form.Item name="refreshInterval" label="Refresh Interval (ms)">
              <Input type="number" min={1000} max={60000} step={1000} />
            </Form.Item>
            <Form.Item name="defaultMaxSteps" label="Default Max Steps">
              <Input type="number" min={1} max={200} />
            </Form.Item>
          </Form>
        </Card>

        <Card className="demo-card" style={{ borderRadius: 12, border: '1px solid var(--color-border)' }}>
          <Title level={4} style={{ marginBottom: 16 }}>Notification Settings</Title>
          <Form form={notifForm} layout="vertical" initialValues={{
            emailNotifications: true,
            runComplete: true,
            runFailed: true,
            runError: true,
          }}>
            <Form.Item name="emailNotifications" label="Email Notifications" valuePropName="checked">
              <Switch />
            </Form.Item>
            <Divider />
            <Form.Item name="runComplete" label="Notify on Run Complete" valuePropName="checked">
              <Switch disabled={!emailNotifications} />
            </Form.Item>
            <Form.Item name="runFailed" label="Notify on Run Failed" valuePropName="checked">
              <Switch disabled={!emailNotifications} />
            </Form.Item>
            <Form.Item name="runError" label="Notify on System Error" valuePropName="checked">
              <Switch disabled={!emailNotifications} />
            </Form.Item>
          </Form>
        </Card>

        <Card className="demo-card" style={{ borderRadius: 12, border: '1px solid var(--color-border)' }}>
          <Title level={4} style={{ marginBottom: 16 }}>About</Title>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div>
              <Text style={{ fontSize: 13, color: 'var(--color-text-muted)', display: 'block', marginBottom: 4 }}>Version</Text>
              <Text style={{ fontSize: 18, fontWeight: 600 }}>1.0.0</Text>
            </div>
            <div>
              <Text style={{ fontSize: 13, color: 'var(--color-text-muted)', display: 'block', marginBottom: 4 }}>Description</Text>
              <Paragraph style={{ margin: 0, fontSize: 14 }}>
                Synthetic User Lab - Automated UX testing platform using AI agents to simulate user behavior.
              </Paragraph>
            </div>
            <div>
              <Text style={{ fontSize: 13, color: 'var(--color-text-muted)', display: 'block', marginBottom: 4 }}>Links</Text>
              <Space direction="vertical">
                <a href="https://github.com" target="_blank" rel="noopener noreferrer">GitHub Repository</a>
                <a href="https://docs.example.com" target="_blank" rel="noopener noreferrer">Documentation</a>
              </Space>
            </div>
          </div>
        </Card>
      </div>

      <div style={{ marginTop: 24, display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
        <Button onClick={() => navigate('/')}>Cancel</Button>
        <Button type="primary" onClick={handleSave} className="btn-primary-gradient">
          Save Settings
        </Button>
      </div>
    </div>
  );
}
