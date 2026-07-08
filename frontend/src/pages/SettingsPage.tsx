import { Typography, Card, Divider, Switch, Select, Input, Button, Space, message, Form, Alert } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router';
import { useTranslation } from 'react-i18next';
import { useFrontendSettings, useUpdateFrontendSettings } from '../hooks/useFrontendSettings';
import { AppErrorState, AppLoading } from '../components/feedback/AppFeedback';
import { getErrorMessage } from '../lib/api-error';

const { Title, Text, Paragraph } = Typography;

export default function SettingsPage() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const settingsQuery = useFrontendSettings();
  const updateSettings = useUpdateFrontendSettings();
  const [generalForm] = Form.useForm();
  const [runForm] = Form.useForm();
  const [notifForm] = Form.useForm();
  const [saved, setSaved] = useState(false);
  const savedTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const emailNotifications = Form.useWatch('emailNotifications', notifForm);

  useEffect(() => {
    return () => {
      if (savedTimerRef.current) {
        clearTimeout(savedTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!settingsQuery.data) {
      return;
    }
    const settings = settingsQuery.data;
    generalForm.setFieldsValue({
      language: settings.locale,
      timezone: settings.timezone,
      dateFormat: settings.date_format,
      theme: settings.theme,
    });
    runForm.setFieldsValue({
      defaultHeadless: settings.default_headless,
      defaultMaxSteps: settings.default_max_steps,
      autoRefresh: settings.auto_refresh,
      refreshInterval: settings.refresh_interval_ms,
      defaultRunName: settings.default_run_name,
    });
    notifForm.setFieldsValue({
      emailNotifications: settings.email_notifications,
      runComplete: settings.notify_run_complete,
      runFailed: settings.notify_run_failed,
      runError: settings.notify_system_error,
    });
  }, [settingsQuery.data, generalForm, runForm, notifForm]);

  const handleSave = async () => {
    try {
      const [generalValues, runValues, notifValues] = await Promise.all([
        generalForm.validateFields(),
        runForm.validateFields(),
        notifForm.validateFields(),
      ]);
      await updateSettings.mutateAsync({
        locale: generalValues.language,
        timezone: generalValues.timezone,
        date_format: generalValues.dateFormat,
        theme: generalValues.theme,
        default_headless: runValues.defaultHeadless,
        default_max_steps: Number(runValues.defaultMaxSteps),
        auto_refresh: runValues.autoRefresh,
        refresh_interval_ms: Number(runValues.refreshInterval),
        default_run_name: runValues.defaultRunName,
        email_notifications: notifValues.emailNotifications,
        notify_run_complete: notifValues.runComplete,
        notify_run_failed: notifValues.runFailed,
        notify_system_error: notifValues.runError,
      });
      setSaved(true);
      message.success(t('settings.saveSuccess'));
      if (savedTimerRef.current) {
        clearTimeout(savedTimerRef.current);
      }
      savedTimerRef.current = setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      message.error(getErrorMessage(error, t('settings.saveError')));
    }
  };

  if (settingsQuery.isLoading) {
    return <AppLoading tip={t('common.loading')} minHeight={260} />;
  }

  if (settingsQuery.isError) {
    return (
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/')}
          />
          <Title level={1} className="page-title">
            {t('settings.title')}
          </Title>
        </div>
        <AppErrorState
          title={t('settings.loadFailed')}
          description={getErrorMessage(settingsQuery.error, t('common.retryLater'))}
          onRetry={() => settingsQuery.refetch()}
        />
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/')}
        />
        <Title level={1} className="page-title">
          {t('settings.title')}
        </Title>
      </div>

      {saved && (
        <Alert
          message={t('settings.saved')}
          type="success"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <Card className="demo-card">
          <Title level={4} style={{ marginBottom: 16 }}>{t('settings.general')}</Title>
          <Form form={generalForm} layout="vertical">
            <Form.Item name="language" label={t('settings.language')}>
              <Select
                options={[
                  { value: 'en-US', label: t('locale.en-US') },
                  { value: 'zh-CN', label: t('locale.zh-CN') },
                ]}
              />
            </Form.Item>
            <Form.Item name="timezone" label={t('settings.timezone')}>
              <Select
                options={[
                  { value: 'UTC', label: 'UTC' },
                  { value: 'Asia/Shanghai', label: 'Asia/Shanghai' },
                  { value: 'America/New_York', label: 'America/New_York' },
                ]}
              />
            </Form.Item>
            <Form.Item name="dateFormat" label={t('settings.dateFormat')}>
              <Select
                options={[
                  { value: 'YYYY-MM-DD', label: 'YYYY-MM-DD' },
                  { value: 'DD/MM/YYYY', label: 'DD/MM/YYYY' },
                  { value: 'MM/DD/YYYY', label: 'MM/DD/YYYY' },
                ]}
              />
            </Form.Item>
            <Form.Item name="theme" label={t('settings.theme')}>
              <Select
                options={[
                  { value: 'light', label: t('theme.light') },
                  { value: 'dark', label: t('theme.dark') },
                  { value: 'auto', label: t('theme.auto') },
                ]}
              />
            </Form.Item>
          </Form>
        </Card>

        <Card className="demo-card">
          <Title level={4} style={{ marginBottom: 16 }}>{t('settings.run')}</Title>
          <Form form={runForm} layout="vertical">
            <Form.Item name="defaultHeadless" label={t('settings.defaultHeadless')} valuePropName="checked">
              <Switch />
            </Form.Item>
            <Form.Item name="autoRefresh" label={t('settings.autoRefresh')} valuePropName="checked">
              <Switch />
            </Form.Item>
            <Form.Item
              name="refreshInterval"
              label={t('settings.refreshInterval')}
              rules={[{ required: true, type: 'number', min: 1000, max: 60000, transform: (v) => Number(v), message: t('settings.refreshInterval') }]}
            >
              <Input type="number" min={1000} max={60000} step={1000} />
            </Form.Item>
            <Form.Item
              name="defaultMaxSteps"
              label={t('settings.defaultMaxSteps')}
              rules={[{ required: true, type: 'number', min: 1, max: 50, transform: (v) => Number(v), message: t('settings.defaultMaxSteps') }]}
            >
              <Input type="number" min={1} max={50} />
            </Form.Item>
            <Form.Item name="defaultRunName" label={t('settings.defaultRunName')}>
              <Input />
            </Form.Item>
          </Form>
        </Card>

        <Card className="demo-card">
          <Title level={4} style={{ marginBottom: 16 }}>{t('settings.notifications')}</Title>
          <Form form={notifForm} layout="vertical">
            <Form.Item name="emailNotifications" label={t('settings.emailNotifications')} valuePropName="checked">
              <Switch />
            </Form.Item>
            <Divider />
            <Form.Item name="runComplete" label={t('settings.notifyRunComplete')} valuePropName="checked">
              <Switch disabled={!emailNotifications} />
            </Form.Item>
            <Form.Item name="runFailed" label={t('settings.notifyRunFailed')} valuePropName="checked">
              <Switch disabled={!emailNotifications} />
            </Form.Item>
            <Form.Item name="runError" label={t('settings.notifySystemError')} valuePropName="checked">
              <Switch disabled={!emailNotifications} />
            </Form.Item>
          </Form>
        </Card>

        <Card className="demo-card">
          <Title level={4} style={{ marginBottom: 16 }}>{t('settings.about')}</Title>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div>
              <Text style={{ fontSize: 13, color: 'var(--geist-foreground-tertiary)', display: 'block', marginBottom: 4 }}>{t('settings.version')}</Text>
              <Text style={{ fontSize: 18, fontWeight: 600 }}>1.0.0</Text>
            </div>
            <div>
              <Text style={{ fontSize: 13, color: 'var(--geist-foreground-tertiary)', display: 'block', marginBottom: 4 }}>{t('settings.description')}</Text>
              <Paragraph style={{ margin: 0, fontSize: 14 }}>
                Synthetic User Lab - Automated UX testing platform using AI agents to simulate user behavior.
              </Paragraph>
            </div>
            <div>
              <Text style={{ fontSize: 13, color: 'var(--geist-foreground-tertiary)', display: 'block', marginBottom: 4 }}>{t('settings.links')}</Text>
              <Space direction="vertical">
                <a href="https://github.com" target="_blank" rel="noopener noreferrer">{t('settings.github')}</a>
                <a href="https://docs.example.com" target="_blank" rel="noopener noreferrer">{t('settings.docs')}</a>
              </Space>
            </div>
          </div>
        </Card>
      </div>

      <div style={{ marginTop: 24, display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
        <Button onClick={() => navigate('/')}>{t('common.cancel')}</Button>
        <Button type="primary" onClick={handleSave} loading={updateSettings.isPending}>
          {t('common.save')}
        </Button>
      </div>
    </div>
  );
}
