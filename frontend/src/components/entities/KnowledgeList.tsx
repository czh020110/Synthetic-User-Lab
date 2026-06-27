import { Table, Button, Modal, Form, Input, Select, Space, message, Popconfirm, Tag } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useState } from 'react';
import { useKnowledgeItems, useCreateKnowledgeItem, useUpdateKnowledgeItem, useDeleteKnowledgeItem } from '../../hooks/useKnowledge';
import type { KnowledgeItem, RetrievalSourceType } from '../../types/knowledge';

export default function KnowledgeList() {
  const [sourceType, setSourceType] = useState<RetrievalSourceType | undefined>();
  const { data: items, isLoading } = useKnowledgeItems(sourceType);
  const create = useCreateKnowledgeItem();
  const update = useUpdateKnowledgeItem();
  const remove = useDeleteKnowledgeItem();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<KnowledgeItem | null>(null);
  const [form] = Form.useForm();

  const openCreate = () => {
    setEditing(null);
    form.resetFields();
    setModalOpen(true);
  };

  const openEdit = (record: KnowledgeItem) => {
    setEditing(record);
    form.setFieldsValue(record);
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editing) {
        await update.mutateAsync({ id: editing.id, data: values });
        message.success('更新成功');
      } else {
        await create.mutateAsync(values);
        message.success('创建成功');
      }
      setModalOpen(false);
    } catch (err) {
      if ((err as any)?.errorFields) return;
      message.error(`操作失败: ${(err as Error).message}`);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await remove.mutateAsync(id);
      message.success('删除成功');
    } catch (err) {
      message.error(`删除失败: ${(err as Error).message}`);
    }
  };

  const columns = [
    { title: 'Title', dataIndex: 'title', key: 'title' },
    {
      title: 'Type',
      dataIndex: 'source_type',
      key: 'source_type',
      render: (v: string) => (
        <Tag color={v === 'product_knowledge' ? 'blue' : 'orange'}>
          {v === 'product_knowledge' ? 'Knowledge' : 'Failure Case'}
        </Tag>
      ),
    },
    { title: 'Content', dataIndex: 'content', key: 'content', ellipsis: true },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: KnowledgeItem) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(record)} />
          <Popconfirm title="确认删除?" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <>
      <Space style={{ marginBottom: 16 }}>
        <Select
          placeholder="Filter by type"
          allowClear
          style={{ width: 200 }}
          value={sourceType}
          onChange={setSourceType}
          options={[
            { value: 'product_knowledge', label: 'Product Knowledge' },
            { value: 'failure_case', label: 'Failure Case' },
          ]}
        />
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          New Knowledge
        </Button>
      </Space>

      <Table
        dataSource={items || []}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        size="small"
      />

      <Modal
        title={editing ? 'Edit Knowledge' : 'New Knowledge'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={create.isPending || update.isPending}
        width={640}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="source_type" label="Type" rules={[{ required: true }]}>
            <Select options={[
              { value: 'product_knowledge', label: 'Product Knowledge' },
              { value: 'failure_case', label: 'Failure Case' },
            ]} />
          </Form.Item>
          <Form.Item name="title" label="Title" rules={[{ required: true, max: 200 }]}>
            <Input />
          </Form.Item>
          <Form.Item name="content" label="Content" rules={[{ required: true }]}>
            <Input.TextArea rows={4} />
          </Form.Item>
          <Form.Item name="keywords" label="Keywords">
            <Select mode="tags" placeholder="输入关键词" />
          </Form.Item>
          <Form.Item name="source_ref" label="Source Ref">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
