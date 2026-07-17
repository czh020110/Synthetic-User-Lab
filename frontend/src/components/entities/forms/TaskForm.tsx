import { Modal, Form, Input, Select, Switch, message } from 'antd';
import { useTranslation } from 'react-i18next';
import type { Task, ActionName } from '../../../types/task';
import { useCreateTask, useUpdateTask } from '../../../hooks/useTasks';

const riskLevels = ['low', 'medium', 'high'] as const;
const allActions: ActionName[] = [
  'navigate', 'click', 'fill', 'wait',
  'press', 'scroll', 'upload', 'select',
  'hover', 'check', 'uncheck', 'dblclick',
  'drag', 'ask_for_help', 'abandon',
];

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
  const { t } = useTranslation();
  const createTask = useCreateTask();
  const updateTask = useUpdateTask();
  const isEdit = !!editItem;

  const levelLabels: Record<string, string> = {
    low: t('forms.levelLow'),
    medium: t('forms.levelMedium'),
    high: t('forms.levelHigh'),
  };

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
        message.success(t('forms.task.updated'));
      } else {
        await createTask.mutateAsync(payload);
        message.success(t('forms.task.created'));
      }
      form.resetFields();
      onClose();
    } catch (err) {
      message.error(t('forms.failed', { message: (err as Error).message }));
    }
  };

  return (
    <Modal
      title={isEdit ? t('forms.task.titleEdit') : t('forms.task.titleCreate')}
      open={open}
      onCancel={onClose}
      onOk={handleOk}
      okText={isEdit ? t('forms.okUpdate') : t('forms.okCreate')}
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
        <Form.Item name="name" label={t('forms.task.name')} rules={[{ required: true, message: t('forms.task.nameRequired') }]}>
          <Input placeholder="e.g. Complete registration" />
        </Form.Item>

        <Form.Item name="description" label={t('forms.task.description')}>
          <Input.TextArea rows={2} placeholder="Describe the task goal" />
        </Form.Item>

        <Form.Item name="start_url" label={t('forms.task.startUrl')} rules={[{ required: true, message: t('forms.task.startUrlRequired') }]}>
          <Input placeholder="https://example.com" />
        </Form.Item>

        <Form.Item name="success_criteria" label={t('forms.task.successCriteria')}>
          <Input placeholder="criteria1, criteria2, criteria3" />
        </Form.Item>

        <Form.Item name="max_steps" label={t('forms.task.maxSteps')}>
          <Select
            options={[15, 30, 50, 100].map((v) => ({ label: t('forms.task.stepsUnit', { n: v }), value: v }))}
          />
        </Form.Item>

        <Form.Item name="risk_level" label={t('forms.task.riskLevel')}>
          <Select
            options={riskLevels.map((v) => ({ label: levelLabels[v], value: v }))}
          />
        </Form.Item>

        <Form.Item name="destructive_action_allowed" label={t('forms.task.destructive')} valuePropName="checked">
          <Switch />
        </Form.Item>

        <Form.Item name="allowed_actions" label={t('forms.task.allowedActions')}>
          <Select
            mode="multiple"
            options={allActions.map((v) => ({ label: v, value: v }))}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
}
