import { Modal, Form, Input, Select, message } from 'antd';
import { useTranslation } from 'react-i18next';
import type { Persona } from '../../../types/persona';
import { useCreatePersona, useUpdatePersona } from '../../../hooks/usePersonas';
import { useModelPresets } from '../../../hooks/useSystemConfig';

const skillLevels = ['newbie', 'intermediate', 'expert'] as const;
const patienceLevels = ['low', 'medium', 'high'] as const;
const riskLevels = ['low', 'medium', 'high'] as const;

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
  const { t } = useTranslation();
  const presets = useModelPresets();
  const createPersona = useCreatePersona();
  const updatePersona = useUpdatePersona();
  const isEdit = !!editItem;

  const levelLabels: Record<string, string> = {
    newbie: t('forms.levelNewbie'),
    intermediate: t('forms.levelIntermediate'),
    expert: t('forms.levelExpert'),
    low: t('forms.levelLow'),
    medium: t('forms.levelMedium'),
    high: t('forms.levelHigh'),
  };

  const handleOk = () => {
    form.submit();
  };

  const handleFinish = async (values: any) => {
    // 清空预设时 Select 值为 undefined，统一转 null 以便后端 exclude_unset 能真正清空 model_preset_id
    const payload = { ...values, model_preset_id: values.model_preset_id ?? null };
    try {
      if (isEdit) {
        await updatePersona.mutateAsync({ id: editItem.id, data: payload });
        message.success(t('forms.persona.updated'));
      } else {
        await createPersona.mutateAsync(payload);
        message.success(t('forms.persona.created'));
      }
      form.resetFields();
      onClose();
    } catch (err) {
      message.error(t('forms.failed', { message: (err as Error).message }));
    }
  };

  return (
    <Modal
      title={isEdit ? t('forms.persona.titleEdit') : t('forms.persona.titleCreate')}
      open={open}
      onCancel={onClose}
      onOk={handleOk}
      okText={isEdit ? t('forms.okUpdate') : t('forms.okCreate')}
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
        <Form.Item name="name" label={t('forms.persona.name')} rules={[{ required: true, message: t('forms.persona.nameRequired') }]}>
          <Input placeholder="e.g. First-time User" />
        </Form.Item>

        <Form.Item name="description" label={t('forms.persona.description')}>
          <Input.TextArea rows={2} placeholder="Describe this persona's behavior and goals" />
        </Form.Item>

        <Form.Item name="skill_level" label={t('forms.persona.skill')} rules={[{ required: true }]}>
          <Select
            options={skillLevels.map((v) => ({ label: levelLabels[v], value: v }))}
          />
        </Form.Item>

        <Form.Item name="patience_level" label={t('forms.persona.patience')}>
          <Select
            options={patienceLevels.map((v) => ({ label: levelLabels[v], value: v }))}
          />
        </Form.Item>

        <Form.Item name="risk_preference" label={t('forms.persona.risk')}>
          <Select
            options={riskLevels.map((v) => ({ label: levelLabels[v], value: v }))}
          />
        </Form.Item>

        <Form.Item name="model_preset_id" label={t('forms.persona.modelPreset')} tooltip={t('forms.persona.modelPresetTooltip')}>
          <Select
            allowClear
            placeholder={t('forms.persona.modelPresetPlaceholder')}
            options={(presets.data ?? []).map((p) => ({ label: p.name, value: p.id }))}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
}
