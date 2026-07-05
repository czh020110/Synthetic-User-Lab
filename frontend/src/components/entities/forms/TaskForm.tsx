import { Modal, Form, Input, Select, Switch, message } from 'antd';
import type { Task, ActionName } from '../../../types/task';
import { useCreateTask, useUpdateTask } from '../../../hooks/useTasks';

const riskLevels = ['low', 'medium', 'high'] as const;
const allActions: ActionName[] = [
  'navigate', 'click', 'fill', 'wait',
  'press', 'scroll', 'upload', 'select',
  'hover', 'check', 'uncheck', 'dblclick',
  'drag', 'ask_for_help', 'abandon',
];

const labelMap: Record<string, string> = {
  low: 'Low',
  medium: 'Medium',
  high: 'High',
};

export default function TaskForm({
  open,
  editItem,
  onClose,
}: {
  open: boolean;
  editItem: Task | null;
  onClose: () => void;
}) {
  const [form] = Form.useForm();
  const createTask = useCreateTask();
  const updateTask = useUpdateTask();
  const isEdit = !!editItem;

  const handleOk = () => {
    form.submit();
  };

  const handleFinish = async (values: any) => {
    const payload = {
      name: values.name,
      description: values.description,
      start_url: values.start_url,
      success_criteria: values.success_criteria ? values.success_criteria.split(',').map((s: string) => s.trim()).filter(Boolean) : [],
      max_steps: values.max_steps,
      allowed_actions: values.allowed_actions,
      risk_level: values.risk_level,
      destructive_action_allowed: values.destructive_action_allowed,
    };

    try {
      if (isEdit) {
        await updateTask.mutateAsync({ id: editItem.id, data: payload });
        message.success('Task updated');
      } else {
        await createTask.mutateAsync(payload);
        message.success('Task created');
      }
      form.resetFields();
      onClose();
    } catch (err) {
      message.error(`Failed: ${(err as Error).message}`);
    }
  };

  return (
    <Modal
      title={isEdit ? 'Edit Task' : 'Create Task'}
      open={open}
      onCancel={onClose}
      onOk={handleOk}
      okText={isEdit ? 'Update' : 'Create'}
      okButtonProps={{ loading: createTask.isPending || updateTask.isPending }}
      width={560}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={editItem ? {
          name: editItem.name,
          description: editItem.description,
          start_url: editItem.start_url,
          success_criteria: editItem.success_criteria?.join(', '),
          max_steps: editItem.max_steps,
          allowed_actions: editItem.allowed_actions,
          risk_level: editItem.risk_level,
          destructive_action_allowed: editItem.destructive_action_allowed,
        } : {
          max_steps: 30,
          risk_level: 'low',
          destructive_action_allowed: false,
          allowed_actions: allActions.slice(0, 8),
        }}
        onFinish={handleFinish}
      >
        <Form.Item name="name" label="Name" rules={[{ required: true, message: '请输入 Task 名称' }]}>
          <Input placeholder="e.g. Complete registration" />
        </Form.Item>

        <Form.Item name="description" label="Description">
          <Input.TextArea rows={2} placeholder="Describe the task goal" />
        </Form.Item>

        <Form.Item name="start_url" label="Start URL" rules={[{ required: true, message: '请输入起始 URL' }]}>
          <Input placeholder="https://example.com" />
        </Form.Item>

        <Form.Item name="success_criteria" label="Success Criteria">
          <Input placeholder="criteria1, criteria2, criteria3" />
        </Form.Item>

        <Form.Item name="max_steps" label="Max Steps">
          <Select
            options={[15, 30, 50, 100].map((v) => ({ label: `${v} steps`, value: v }))}
          />
        </Form.Item>

        <Form.Item name="risk_level" label="Risk Level">
          <Select
            options={riskLevels.map((v) => ({ label: labelMap[v], value: v }))}
          />
        </Form.Item>

        <Form.Item name="destructive_action_allowed" label="Allow Destructive Actions" valuePropName="checked">
          <Switch />
        </Form.Item>

        <Form.Item name="allowed_actions" label="Allowed Actions">
          <Select
            mode="multiple"
            options={allActions.map((v) => ({ label: v, value: v }))}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
}
