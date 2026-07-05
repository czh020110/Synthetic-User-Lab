import { Card, Form, Select, Input, Switch, Button, Space, message, Typography, Tag } from 'antd';
import { ArrowLeftOutlined, RocketOutlined, UserOutlined, FileTextOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router';
import { usePersonas } from '../hooks/usePersonas';
import { useTasks } from '../hooks/useTasks';
import { useStartFormalRun } from '../hooks/useRuns';

const { Text, Title } = Typography;

export default function StartRunPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const preselectedPersona = searchParams.get('persona_id');
  const preselectedTask = searchParams.get('task_id');

  const { data: personas } = usePersonas();
  const { data: tasks } = useTasks();
  const startRun = useStartFormalRun();
  const [form] = Form.useForm();

  // 当 persona/task 列表加载完成后再回填预选值，
  // 避免 initialValues 早于 options 就绪导致 Select 选不中。
  useEffect(() => {
    if (preselectedPersona && personas?.some(p => p.id === preselectedPersona)) {
      form.setFieldValue('persona_id', preselectedPersona);
    }
  }, [personas, preselectedPersona, form]);

  useEffect(() => {
    if (preselectedTask && tasks?.some(t => t.id === preselectedTask)) {
      form.setFieldValue('task_id', preselectedTask);
    }
  }, [tasks, preselectedTask, form]);

  const handleSubmit = async (values: any) => {
    try {
      const result = await startRun.mutateAsync({
        persona_id: values.persona_id,
        task_id: values.task_id,
        run_name: values.run_name || 'run',
        headless: values.headless ? true : undefined,
      });
      message.success('Run 已启动');
      navigate(`/runs/${result.run_id}`);
    } catch (err) {
      message.error(`启动失败: ${(err as Error).message}`);
    }
  };

  const personasEmpty = personas && personas.length === 0;
  const tasksEmpty = tasks && tasks.length === 0;

  return (
    <div>
      {/* Breadcrumb */}
      <div className="page-header" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/')}
            style={{ borderRadius: 8 }}
          />
          <Title level={1} style={{ margin: 0, fontSize: 24, fontWeight: 700, color: 'var(--color-text-primary)' }}>
            Start Formal Run
          </Title>
        </div>
        <Text style={{ fontSize: 14, color: 'var(--color-text-muted)' }}>
          选择 Persona 和 Task 启动一次正式运行
        </Text>
      </div>

      {personasEmpty || tasksEmpty ? (
        <div className="empty-state" style={{ padding: 64 }}>
          <div className="empty-icon" style={{ fontSize: 40, marginBottom: 12 }}>📦</div>
          <h4 style={{ margin: '0 0 8px 0', fontSize: 15, fontWeight: 600, color: 'var(--color-text-primary)' }}>
            {personasEmpty && tasksEmpty
              ? 'No Personas or Tasks'
              : personasEmpty
                ? 'No Personas'
                : 'No Tasks'}
          </h4>
          <p style={{ margin: '0 0 16px 0', color: 'var(--color-text-muted)', fontSize: 14 }}>
            Please create{' '}
            {personasEmpty && tasksEmpty
              ? 'a Persona and a Task'
              : personasEmpty
                ? 'a Persona'
                : 'a Task'}{' '}
            first in the{' '}
            <span
              style={{ color: 'var(--color-primary)', cursor: 'pointer', fontWeight: 500 }}
              onClick={() => navigate('/entities')}
            >
              Entities
            </span>{' '}
            page.
          </p>
          <Button
            type="primary"
            onClick={() => navigate('/entities')}
            className="btn-primary-gradient"
          >
            Go to Entities
          </Button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24 }}>
          <Card
            className="demo-card form-card"
            style={{ borderRadius: 12, border: '1px solid var(--color-border)' }}
          >
            <Form
              form={form}
              layout="vertical"
              initialValues={{
                run_name: 'run',
                headless: true,
                persona_id: preselectedPersona || undefined,
                task_id: preselectedTask || undefined,
              }}
              onFinish={handleSubmit}
            >
              <Form.Item
                name="persona_id"
                label={<Text strong style={{ fontSize: 14 }}>Persona</Text>}
                rules={[{ required: true, message: '请选择 Persona' }]}
              >
                <Select
                  size="middle"
                  placeholder="Select a persona"
                  loading={!personas}
                  options={(personas || []).map((p) => ({
                    value: p.id,
                    label: (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <UserOutlined style={{ color: 'var(--color-primary)' }} />
                        <span>{p.name}</span>
                        <Tag style={{ marginLeft: 4, fontSize: 11 }}>{p.skill_level}</Tag>
                      </div>
                    ),
                  }))}
                />
              </Form.Item>

              <Form.Item
                name="task_id"
                label={<Text strong style={{ fontSize: 14 }}>Task</Text>}
                rules={[{ required: true, message: '请选择 Task' }]}
              >
                <Select
                  size="middle"
                  placeholder="Select a task"
                  loading={!tasks}
                  options={(tasks || []).map((t) => ({
                    value: t.id,
                    label: (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <FileTextOutlined style={{ color: 'var(--color-success)' }} />
                        <span>{t.name}</span>
                        <Tag color={t.risk_level === 'high' ? 'error' : t.risk_level === 'medium' ? 'warning' : 'success'} style={{ marginLeft: 4, fontSize: 11 }}>
                          {t.risk_level}
                        </Tag>
                      </div>
                    ),
                  }))}
                />
              </Form.Item>

              <Form.Item name="run_name" label={<Text strong style={{ fontSize: 14 }}>Run Name</Text>}>
                <Input placeholder="run" />
              </Form.Item>

              <Form.Item name="headless" label={<Text strong style={{ fontSize: 14 }}>Headless</Text>} valuePropName="checked">
                <Switch />
              </Form.Item>
              <Text type="secondary" style={{ display: 'block', marginTop: -12, marginBottom: 24, fontSize: 13 }}>
                Run browser without UI (headless mode)
              </Text>

              <Form.Item style={{ marginTop: 24, marginBottom: 0 }}>
                <Space>
                  <Button
                    onClick={() => navigate('/')}
                    style={{ borderRadius: 8, height: 40, padding: '0 20px' }}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="primary"
                    htmlType="submit"
                    loading={startRun.isPending}
                    className="btn-primary-gradient"
                    icon={<RocketOutlined />}
                  >
                    Start Run
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>

          {/* Tips Sidebar */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            <Card className="demo-card" style={{ borderRadius: 12, border: '1px solid var(--color-border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                <InfoCircleOutlined style={{ color: 'var(--color-primary)' }} />
                <Text strong>Tips</Text>
              </div>
              <ul style={{ margin: 0, paddingLeft: 20, fontSize: 13, color: 'var(--color-text-secondary)', lineHeight: 1.8 }}>
                <li>选择与任务难度匹配的 Persona</li>
                <li>高风险任务会自动启用安全护栏</li>
                <li>Headless 模式运行更快</li>
                <li>Run 名称便于后续查找</li>
              </ul>
            </Card>

            <Card className="demo-card" style={{ borderRadius: 12, border: '1px solid var(--color-border)' }}>
              <Text strong style={{ display: 'block', marginBottom: 12 }}>Quick Stats</Text>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>Available Personas</Text>
                  <Text strong>{personas?.length || 0}</Text>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>Available Tasks</Text>
                  <Text strong>{tasks?.length || 0}</Text>
                </div>
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
