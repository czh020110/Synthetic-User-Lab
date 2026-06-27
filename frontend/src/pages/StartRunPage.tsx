import { Card, Form, Select, Input, Switch, Button, Space, message } from 'antd';
import { useNavigate } from 'react-router';
import { usePersonas } from '../hooks/usePersonas';
import { useTasks } from '../hooks/useTasks';
import { useStartFormalRun } from '../hooks/useRuns';

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

  return (
    <Card title="Start Formal Run" style={{ maxWidth: 600 }}>
      <Form
        form={form}
        layout="vertical"
        initialValues={{ run_name: 'run', headless: true }}
        onFinish={handleSubmit}
      >
        <Form.Item
          name="persona_id"
          label="Persona"
          rules={[{ required: true, message: '请选择 Persona' }]}
        >
          <Select
            placeholder="选择 Persona"
            options={(personas || []).map((p) => ({
              value: p.id,
              label: `${p.name} (${p.skill_level})`,
            }))}
          />
        </Form.Item>

        <Form.Item
          name="task_id"
          label="Task"
          rules={[{ required: true, message: '请选择 Task' }]}
        >
          <Select
            placeholder="选择 Task"
            options={(tasks || []).map((t) => ({
              value: t.id,
              label: `${t.name} - ${t.start_url.slice(0, 50)}`,
            }))}
          />
        </Form.Item>

        <Form.Item name="run_name" label="Run Name">
          <Input placeholder="run" />
        </Form.Item>

        <Form.Item name="headless" label="Headless" valuePropName="checked">
          <Switch />
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={startRun.isPending}>
              Start Run
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  );
}
