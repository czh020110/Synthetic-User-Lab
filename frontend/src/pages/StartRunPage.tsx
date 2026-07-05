import { Card, Form, Select, Input, Switch, Button, Space, message, Typography, Tag } from 'antd';
import { ArrowLeftOutlined, RocketOutlined, UserOutlined, FileTextOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router';
import { usePersonas } from '../hooks/usePersonas';
import { useTasks } from '../hooks/useTasks';
import { useStartFormalRun } from '../hooks/useRuns';

const { Text, Title } = Typography;

export default function StartRunPage() {
  const navigate = useNavigate();
  const { data: personas } = usePersonas();
  const { data: tasks } = useTasks();
  const startRun = useStartFormalRun();
  const [form] = Form.useForm();

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
        <Card
          className="demo-card form-card"
          style={{ borderRadius: 12, border: '1px solid var(--color-border)' }}
        >
          <Form
            form={form}
            layout="vertical"
            initialValues={{ run_name: 'run', headless: true }}
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
      )}
    </div>
  );
}
