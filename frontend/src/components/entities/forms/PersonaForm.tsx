import { Modal, Form, Input, Select, message } from 'antd';
import type { Persona } from '../../../types/persona';
import { useCreatePersona, useUpdatePersona } from '../../../hooks/usePersonas';
import { useModelPresets } from '../../../hooks/useSystemConfig';

const skillLevels = ['newbie', 'intermediate', 'expert'] as const;
const patienceLevels = ['low', 'medium', 'high'] as const;
const riskLevels = ['low', 'medium', 'high'] as const;

const labelMap: Record<string, string> = {
  newbie: 'Newbie',
  intermediate: 'Intermediate',
  expert: 'Expert',
  low: 'Low',
  medium: 'Medium',
  high: 'High',
};

export default function PersonaForm({
  open,
  editItem,
  onClose,
}: {
  open: boolean;
  editItem: Persona | null;
  onClose: () => void;
}) {
  const [form] = Form.useForm();
  const presets = useModelPresets();
  const createPersona = useCreatePersona();
  const updatePersona = useUpdatePersona();
  const isEdit = !!editItem;

  const handleOk = () => {
    form.submit();
  };

  const handleFinish = async (values: any) => {
    // 清空预设时 Select 值为 undefined，统一转 null 以便后端 exclude_unset 能真正清空 model_preset_id
    const payload = { ...values, model_preset_id: values.model_preset_id ?? null };
    try {
      if (isEdit) {
        await updatePersona.mutateAsync({ id: editItem.id, data: payload });
        message.success('Persona updated');
      } else {
        await createPersona.mutateAsync(payload);
        message.success('Persona created');
      }
      form.resetFields();
      onClose();
    } catch (err) {
      message.error(`Failed: ${(err as Error).message}`);
    }
  };

  return (
    <Modal
      title={isEdit ? 'Edit Persona' : 'Create Persona'}
      open={open}
      onCancel={onClose}
      onOk={handleOk}
      okText={isEdit ? 'Update' : 'Create'}
      okButtonProps={{ loading: createPersona.isPending || updatePersona.isPending }}
      width={480}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={editItem ? {
          name: editItem.name,
          description: editItem.description,
          skill_level: editItem.skill_level,
          patience_level: editItem.patience_level,
          risk_preference: editItem.risk_preference,
          model_preset_id: editItem.model_preset_id,
        } : {
          skill_level: 'intermediate',
          patience_level: 'medium',
          risk_preference: 'medium',
        }}
        onFinish={handleFinish}
      >
        <Form.Item name="name" label="Name" rules={[{ required: true, message: '请输入 Persona 名称' }]}>
          <Input placeholder="e.g. First-time User" />
        </Form.Item>

        <Form.Item name="description" label="Description">
          <Input.TextArea rows={2} placeholder="Describe this persona's behavior and goals" />
        </Form.Item>

        <Form.Item name="skill_level" label="Skill Level" rules={[{ required: true }]}>
          <Select
            options={skillLevels.map((v) => ({ label: labelMap[v], value: v }))}
          />
        </Form.Item>

        <Form.Item name="patience_level" label="Patience Level">
          <Select
            options={patienceLevels.map((v) => ({ label: labelMap[v], value: v }))}
          />
        </Form.Item>

        <Form.Item name="risk_preference" label="Risk Preference">
          <Select
            options={riskLevels.map((v) => ({ label: labelMap[v], value: v }))}
          />
        </Form.Item>

        <Form.Item name="model_preset_id" label="Model Preset" tooltip="Leave empty to use the default model preset">
          <Select
            allowClear
            placeholder="Use default preset"
            options={(presets.data ?? []).map((p) => ({ label: p.name, value: p.id }))}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
}
