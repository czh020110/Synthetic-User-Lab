import { Modal, Form, Input, Select, message } from 'antd';
import type { KnowledgeItem, RetrievalSourceType } from '../../../types/knowledge';
import { useCreateKnowledgeItem, useUpdateKnowledgeItem } from '../../../hooks/useKnowledge';

const sourceTypes: { label: string; value: RetrievalSourceType }[] = [
  { label: '📘 Product Knowledge', value: 'product_knowledge' },
  { label: '⚠️ Failure Case', value: 'failure_case' },
];

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
  const createItem = useCreateKnowledgeItem();
  const updateItem = useUpdateKnowledgeItem();
  const isEdit = !!editItem;

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
        message.success('Knowledge item updated');
      } else {
        await createItem.mutateAsync(payload);
        message.success('Knowledge item created');
      }
      form.resetFields();
      onClose();
    } catch (err) {
      message.error(`Failed: ${(err as Error).message}`);
    }
  };

  return (
    <Modal
      title={isEdit ? 'Edit Knowledge Item' : 'Create Knowledge Item'}
      open={open}
      onCancel={onClose}
      onOk={handleOk}
      okText={isEdit ? 'Update' : 'Create'}
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
        <Form.Item name="source_type" label="Type" rules={[{ required: true }]}>
          <Select options={sourceTypes} />
        </Form.Item>

        <Form.Item name="title" label="Title" rules={[{ required: true, message: '请输入标题' }]}>
          <Input placeholder="e.g. Registration completion criteria" />
        </Form.Item>

        <Form.Item name="content" label="Content" rules={[{ required: true, message: '请输入内容' }]}>
          <Input.TextArea rows={3} placeholder="Describe the knowledge item content" />
        </Form.Item>

        <Form.Item name="keywords" label="Keywords">
          <Input placeholder="keyword1, keyword2, keyword3" />
        </Form.Item>

        <Form.Item name="source_ref" label="Source Reference">
          <Input placeholder="Optional: internal reference ID" />
        </Form.Item>
      </Form>
    </Modal>
  );
}
