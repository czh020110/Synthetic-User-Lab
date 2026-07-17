import { Modal, Form, Input, Select, message } from 'antd';
import { useTranslation } from 'react-i18next';
import type { KnowledgeItem, RetrievalSourceType } from '../../../types/knowledge';
import { useCreateKnowledgeItem, useUpdateKnowledgeItem } from '../../../hooks/useKnowledge';

export default function KnowledgeForm({
  open,
  editItem,
  onClose,
}: {
  open: boolean;
  editItem: KnowledgeItem | null;
  onClose: () => void;
}) {
  const [form] = Form.useForm();
  const { t } = useTranslation();
  const createItem = useCreateKnowledgeItem();
  const updateItem = useUpdateKnowledgeItem();
  const isEdit = !!editItem;

  const sourceTypes: { label: string; value: RetrievalSourceType }[] = [
    { label: t('forms.knowledge.typeProduct'), value: 'product_knowledge' },
    { label: t('forms.knowledge.typeFailure'), value: 'failure_case' },
  ];

  const handleOk = () => {
    form.submit();
  };

  const handleFinish = async (values: any) => {
    const payload = {
      source_type: values.source_type,
      title: values.title,
      content: values.content,
      keywords: values.keywords ? values.keywords.split(',').map((s: string) => s.trim()).filter(Boolean) : [],
      source_ref: values.source_ref,
    };

    try {
      if (isEdit) {
        await updateItem.mutateAsync({ id: editItem!.id, data: payload });
        message.success(t('forms.knowledge.updated'));
      } else {
        await createItem.mutateAsync(payload);
        message.success(t('forms.knowledge.created'));
      }
      form.resetFields();
      onClose();
    } catch (err) {
      message.error(t('forms.failed', { message: (err as Error).message }));
    }
  };

  return (
    <Modal
      title={isEdit ? t('forms.knowledge.titleEdit') : t('forms.knowledge.titleCreate')}
      open={open}
      onCancel={onClose}
      onOk={handleOk}
      okText={isEdit ? t('forms.okUpdate') : t('forms.okCreate')}
      okButtonProps={{ loading: createItem.isPending || updateItem.isPending }}
      width={560}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={editItem ? {
          ...editItem,
          keywords: editItem.keywords?.join(', '),
        } : {
          source_type: 'product_knowledge',
        }}
        onFinish={handleFinish}
      >
        <Form.Item name="source_type" label={t('forms.knowledge.type')} rules={[{ required: true }]}>
          <Select options={sourceTypes} />
        </Form.Item>

        <Form.Item name="title" label={t('forms.knowledge.titleField')} rules={[{ required: true, message: t('forms.knowledge.titleRequired') }]}>
          <Input placeholder="e.g. Registration completion criteria" />
        </Form.Item>

        <Form.Item name="content" label={t('forms.knowledge.content')} rules={[{ required: true, message: t('forms.knowledge.contentRequired') }]}>
          <Input.TextArea rows={3} placeholder="Describe the knowledge item content" />
        </Form.Item>

        <Form.Item name="keywords" label={t('forms.knowledge.keywords')}>
          <Input placeholder="keyword1, keyword2, keyword3" />
        </Form.Item>

        <Form.Item name="source_ref" label={t('forms.knowledge.sourceRef')}>
          <Input placeholder="Optional: internal reference ID" />
        </Form.Item>
      </Form>
    </Modal>
  );
}
