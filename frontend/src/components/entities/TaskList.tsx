import { Table, Button, Modal, Form, Input, Select, Space, message, Popconfirm, InputNumber, Switch } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useState } from 'react';
import { useTasks, useCreateTask, useUpdateTask, useDeleteTask } from '../../hooks/useTasks';
import type { Task, ActionName, RiskLevel } from '../../types/task';

const actionOptions: { value: ActionName; label: string }[] = [
  { value: 'navigate', label: 'Navigate' },
  { value: 'click', label: 'Click' },
  { value: 'fill', label: 'Fill' },
  { value: 'wait', label: 'Wait' },
  { value: 'press', label: 'Press' },
  { value: 'scroll', label: 'Scroll' },
  { value: 'upload', label: 'Upload' },
  { value: 'select', label: 'Select' },
  { value: 'hover', label: 'Hover' },
  { value: 'check', label: 'Check' },
  { value: 'uncheck', label: 'Uncheck' },
  { value: 'dblclick', label: 'Double Click' },
  { value: 'drag', label: 'Drag' },
  { value: 'ask_for_help', label: 'Ask for Help' },
  { value: 'abandon', label: 'Abandon' },
];

export default function TaskList() {
  const { data: tasks, isLoading } = useTasks();
  const create = useCreateTask();
  const update = useUpdateTask();
  const remove = useDeleteTask();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Task | null>(null);
  const [form] = Form.useForm();

  const openCreate = () => {
    setEditing(null);
    form.resetFields();
    setModalOpen(true);
  };

  const openEdit = (record: Task) => {
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
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'URL', dataIndex: 'start_url', key: 'start_url', ellipsis: true },
    { title: 'Max Steps', dataIndex: 'max_steps', key: 'max_steps' },
    { title: 'Risk', dataIndex: 'risk_level', key: 'risk_level' },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Task) => (
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
        New Task
      </Button>
      <Table
        dataSource={tasks || []}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        size="small"
      />

      <Modal
        title={editing ? 'Edit Task' : 'New Task'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={create.isPending || update.isPending}
        width={640}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Name" rules={[{ required: true, max: 200 }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="start_url" label="Start URL" rules={[{ required: true }]}>
            <Input placeholder="https://example.com" />
          </Form.Item>
          <Form.Item name="success_criteria" label="Success Criteria">
            <Select mode="tags" placeholder="输入成功条件" />
          </Form.Item>
          <Form.Item name="max_steps" label="Max Steps" initialValue={8}>
            <InputNumber min={1} max={50} />
          </Form.Item>
          <Form.Item name="allowed_actions" label="Allowed Actions">
            <Select mode="multiple" options={actionOptions} />
          </Form.Item>
          <Form.Item name="risk_level" label="Risk Level">
            <Select options={[
              { value: 'low', label: 'Low' },
              { value: 'medium', label: 'Medium' },
              { value: 'high', label: 'High' },
            ]} />
          </Form.Item>
          <Form.Item name="destructive_action_allowed" label="Destructive Action Allowed" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
