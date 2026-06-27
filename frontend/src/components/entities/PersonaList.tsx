import { Table, Button, Modal, Form, Input, Select, Space, message, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useState } from 'react';
import { usePersonas, useCreatePersona, useUpdatePersona, useDeletePersona } from '../../hooks/usePersonas';
import type { Persona, SkillLevel, PatienceLevel, RiskPreference } from '../../types/persona';

export default function PersonaList() {
  const { data: personas, isLoading } = usePersonas();
  const create = useCreatePersona();
  const update = useUpdatePersona();
  const remove = useDeletePersona();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Persona | null>(null);
  const [form] = Form.useForm();

  const openCreate = () => {
    setEditing(null);
    form.resetFields();
    setModalOpen(true);
  };

  const openEdit = (record: Persona) => {
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
      if ((err as any)?.errorFields) return; // form validation
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
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Skill Level', dataIndex: 'skill_level', key: 'skill_level' },
    { title: 'Patience', dataIndex: 'patience_level', key: 'patience_level' },
    { title: 'Risk', dataIndex: 'risk_preference', key: 'risk_preference' },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Persona) => (
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
      <Button type="primary" icon={<PlusOutlined />} onClick={openCreate} style={{ marginBottom: 16 }}>
        New Persona
      </Button>
      <Table
        dataSource={personas || []}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        size="small"
      />

      <Modal
        title={editing ? 'Edit Persona' : 'New Persona'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={create.isPending || update.isPending}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Name" rules={[{ required: true, max: 200 }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="skill_level" label="Skill Level">
            <Select options={[
              { value: 'newbie', label: 'Newbie' },
              { value: 'intermediate', label: 'Intermediate' },
              { value: 'expert', label: 'Expert' },
            ]} />
          </Form.Item>
          <Form.Item name="patience_level" label="Patience">
            <Select options={[
              { value: 'low', label: 'Low' },
              { value: 'medium', label: 'Medium' },
              { value: 'high', label: 'High' },
            ]} />
          </Form.Item>
          <Form.Item name="risk_preference" label="Risk Preference">
            <Select options={[
              { value: 'low', label: 'Low' },
              { value: 'medium', label: 'Medium' },
              { value: 'high', label: 'High' },
            ]} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
