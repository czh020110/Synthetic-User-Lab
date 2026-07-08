import { Card, Form, Select, Input, Switch, Button, Space, message, Typography, Tag } from 'antd';
import { ArrowLeftOutlined, RocketOutlined, UserOutlined, FileTextOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router';
import { useTranslation } from 'react-i18next';
import { usePersonas } from '../hooks/usePersonas';
import { useTasks } from '../hooks/useTasks';
import { useStartFormalRun, useStartBatchRun } from '../hooks/useRuns';
import { useFrontendSettings } from '../hooks/useFrontendSettings';
import { AppEmpty, AppLoading } from '../components/feedback/AppFeedback';

const { Text, Title } = Typography;

export default function StartRunPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { t } = useTranslation();
  const preselectedPersona = searchParams.get('persona_id');
  const preselectedTask = searchParams.get('task_id');

  const { data: personas } = usePersonas();
  const { data: tasks } = useTasks();
  const { data: settings } = useFrontendSettings();
  const startRun = useStartFormalRun();
  const startBatch = useStartBatchRun();
  const [form] = Form.useForm();

  useEffect(() => {
    if (preselectedPersona && personas?.some(p => p.id === preselectedPersona)) {
      form.setFieldValue('persona_ids', [preselectedPersona]);
    }
  }, [personas, preselectedPersona, form]);

  useEffect(() => {
    if (preselectedTask && tasks?.some(t => t.id === preselectedTask)) {
      form.setFieldValue('task_id', preselectedTask);
    }
  }, [tasks, preselectedTask, form]);

  const handleSubmit = async (values: any) => {
    const personaIds: string[] = values.persona_ids || [];
    const runName = values.run_name || settings?.default_run_name || 'run';
    const headless = values.headless ?? settings?.default_headless ?? true;
    const rawMaxSteps = values.max_steps_override;
    const maxStepsOverride =
      rawMaxSteps === undefined || rawMaxSteps === '' || rawMaxSteps === null
        ? undefined
        : Number(rawMaxSteps);
    try {
      if (personaIds.length === 1) {
        const result = await startRun.mutateAsync({
          persona_id: personaIds[0],
          task_id: values.task_id,
          run_name: runName,
          headless,
          max_steps_override: maxStepsOverride,
        });
        message.success('Run 已启动');
        navigate(`/runs/${result.run_id}`);
      } else {
        const result = await startBatch.mutateAsync({
          task_id: values.task_id,
          persona_ids: personaIds,
          run_name: runName,
          headless,
          max_steps_override: maxStepsOverride,
        });
        message.success(`已启动 ${result.run_ids.length} 个 run`);
        navigate(`/runs/compare?ids=${result.run_ids.join(',')}`);
      }
    } catch (err) {
      message.error(`启动失败: ${(err as Error).message}`);
    }
  };

  const personasEmpty = personas && personas.length === 0;
  const tasksEmpty = tasks && tasks.length === 0;
  const submitting = startRun.isPending || startBatch.isPending;

  return (
    <div>
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/')}
          />
          <Title level={1} className="page-title">
            {t('startRun.title')}
          </Title>
        </div>
        <Text className="page-subtitle">
          {t('startRun.subtitle')}
        </Text>
      </div>

      {personasEmpty || tasksEmpty ? (
        <AppEmpty
          title={personasEmpty && tasksEmpty ? t('startRun.emptyTitleAll') : personasEmpty ? t('startRun.emptyTitlePersona') : t('startRun.emptyTitleTask')}
          description={(
            <>
              {t('startRun.emptyDescriptionPrefix')}{' '}
              {personasEmpty && tasksEmpty
                ? 'a Persona and a Task'
                : personasEmpty
                  ? 'a Persona'
                  : 'a Task'}{' '}
              {t('startRun.emptyDescriptionSuffix')}
            </>
          )}
          action={
            <Button
              type="primary"
              onClick={() => navigate('/entities')}
            >
              {t('startRun.goEntities')}
            </Button>
          }
        />
      ) : !settings ? (
        <AppLoading tip={t('common.loading')} minHeight={260} />
      ) : (
        <div style={{ maxWidth: 640 }}>
          <Card className="demo-card" style={{ padding: 32 }}>
            <Form
              form={form}
              layout="vertical"
              initialValues={{
                run_name: settings?.default_run_name || 'run',
                headless: settings?.default_headless ?? true,
                max_steps_override: settings?.default_max_steps || 30,
                persona_ids: preselectedPersona ? [preselectedPersona] : [],
                task_id: preselectedTask || undefined,
              }}
              onFinish={handleSubmit}
            >
              <Form.Item
                name="persona_ids"
                label={<Text strong style={{ fontSize: 13 }}>{t('startRun.persona')}</Text>}
                rules={[{ required: true, message: '请至少选择一个 Persona', type: 'array' }]}
              >
                <Select
                  mode="multiple"
                  placeholder="选择一个或多个 persona"
                  loading={!personas}
                  options={(personas || []).map((p) => ({
                    value: p.id,
                    label: (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <UserOutlined style={{ color: 'var(--geist-foreground-tertiary)' }} />
                        <span>{p.name}</span>
                        <Tag style={{ marginLeft: 4, fontSize: 11 }}>{p.skill_level}</Tag>
                      </div>
                    ),
                  }))}
                />
              </Form.Item>

              <Form.Item
                name="task_id"
                label={<Text strong style={{ fontSize: 13 }}>{t('startRun.task')}</Text>}
                rules={[{ required: true, message: '请选择 Task' }]}
              >
                <Select
                  placeholder="Select a task"
                  loading={!tasks}
                  options={(tasks || []).map((tItem) => ({
                    value: tItem.id,
                    label: (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <FileTextOutlined style={{ color: 'var(--geist-foreground-tertiary)' }} />
                        <span>{tItem.name}</span>
                        <Tag color={tItem.risk_level === 'high' ? 'error' : tItem.risk_level === 'medium' ? 'warning' : 'success'} style={{ marginLeft: 4, fontSize: 11 }}>
                          {tItem.risk_level}
                        </Tag>
                      </div>
                    ),
                  }))}
                />
              </Form.Item>

              <Form.Item name="run_name" label={<Text strong style={{ fontSize: 13 }}>{t('startRun.runName')}</Text>}>
                <Input placeholder="run" />
              </Form.Item>

              <Form.Item
                name="max_steps_override"
                label={<Text strong style={{ fontSize: 13 }}>{t('settings.defaultMaxSteps')}</Text>}
                rules={[{
                  validator: (_: unknown, v: unknown) => {
                    if (v === undefined || v === '' || v === null) return Promise.resolve();
                    const n = Number(v);
                    if (Number.isNaN(n) || n < 1 || n > 50) {
                      return Promise.reject(new Error(t('startRun.maxStepsInvalid')));
                    }
                    return Promise.resolve();
                  },
                }]}
              >
                <Input type="number" min={1} max={50} />
              </Form.Item>

              <Form.Item name="headless" label={<Text strong style={{ fontSize: 13 }}>{t('startRun.headless')}</Text>} valuePropName="checked">
                <Switch />
              </Form.Item>
              <Text type="secondary" style={{ display: 'block', marginTop: -12, marginBottom: 24, fontSize: 12 }}>
                {t('startRun.headlessHelp')}
              </Text>

              {/* Tips */}
              <div style={{ marginBottom: 24, padding: '14px 16px', background: 'var(--geist-overlay)', borderRadius: 5, border: '1px solid var(--geist-border-secondary)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <InfoCircleOutlined style={{ color: 'var(--geist-foreground-tertiary)', fontSize: 13 }} />
                  <Text strong style={{ fontSize: 13 }}>Tips</Text>
                </div>
                <ul style={{ margin: 0, paddingLeft: 20, fontSize: 12, color: 'var(--geist-foreground-tertiary)', lineHeight: 1.8 }}>
                  <li>选择多个 Persona 可发起批量 run 并生成对比报告</li>
                  <li>选择与任务难度匹配的 Persona</li>
                  <li>高风险任务会自动启用安全护栏</li>
                  <li>Headless 模式运行更快</li>
                </ul>
              </div>

              {/* Quick Stats */}
              <div style={{ marginBottom: 24, display: 'flex', gap: 24, fontSize: 12, color: 'var(--geist-foreground-tertiary)' }}>
                <span>{t('startRun.availablePersonas')}: <strong style={{ color: 'var(--geist-foreground)' }}>{personas?.length || 0}</strong></span>
                <span>{t('startRun.availableTasks')}: <strong style={{ color: 'var(--geist-foreground)' }}>{tasks?.length || 0}</strong></span>
              </div>

              <Form.Item style={{ marginTop: 24, marginBottom: 0 }}>
                <Space>
                  <Button onClick={() => navigate('/')}>
                    {t('common.cancel')}
                  </Button>
                  <Button
                    type="primary"
                    htmlType="submit"
                    loading={submitting}
                    icon={<RocketOutlined />}
                  >
                    {t('startRun.start')}
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>
        </div>
      )}
    </div>
  );
}
