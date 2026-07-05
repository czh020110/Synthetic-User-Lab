import { Button, Space, Card, Typography, Modal, Tag, Avatar, Tooltip } from 'antd';
import { PlusOutlined, FileTextOutlined, EyeOutlined } from '@ant-design/icons';
import { useState } from 'react';
import { useTasks, useDeleteTask } from '../../hooks/useTasks';
import TaskForm from './forms/TaskForm';
import type { Task } from '../../types/task';
import EntityDetailDrawer from './EntityDetailDrawer';

const { Text } = Typography;

export default function TaskList() {
  const { data: tasks, isLoading, isError, refetch } = useTasks();
  const deleteTask = useDeleteTask();
  const [modalOpen, setModalOpen] = useState(false);
  const [editItem, setEditItem] = useState<Task | null>(null);
  const [detailItem, setDetailItem] = useState<Task | null>(null);

  const items = tasks ?? [];

  if (isError) {
    return (
      <div className="error-card">
        <div className="error-icon">⚠️</div>
        <h4 style={{ margin: '0 0 4px 0', fontWeight: 600 }}>Failed to load tasks</h4>
        <p style={{ margin: '0 0 16px 0' }}>Please try again.</p>
        <Button onClick={() => refetch()}>Retry</Button>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <Text style={{ fontSize: 14, color: 'var(--color-text-muted)', fontWeight: 500 }}>
          {isLoading ? 'Loading...' : `${items.length} task${items.length !== 1 ? 's' : ''}`}
        </Text>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => { setEditItem(null); setModalOpen(true); }}
          className="btn-primary-gradient"
          style={{ fontWeight: 500 }}
        >
          + New Task
        </Button>
      </div>

      {items.length === 0 && !isLoading ? (
        <div className="empty-state" style={{ padding: 48 }}>
          <div className="empty-icon" style={{ fontSize: 40, marginBottom: 12 }}>📋</div>
          <h4 style={{ margin: '0 0 8px 0', fontSize: 15, fontWeight: 600, color: 'var(--color-text-primary)' }}>
            No tasks yet
          </h4>
          <p style={{ margin: '0 0 16px 0', color: 'var(--color-text-muted)', fontSize: 14 }}>
            Create one to get started.
          </p>
          <Button type="primary" onClick={() => setModalOpen(true)} className="btn-primary-gradient">
            Create Task
          </Button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {items.map((t) => (
            <Card
              key={t.id}
              className="demo-card"
              size="small"
              style={{ borderRadius: 12, border: '1px solid var(--color-border)' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', padding: '4px' }}>
                <div style={{ display: 'flex', gap: 12, flex: 1 }}>
                  <Avatar
                    size={40}
                    icon={<FileTextOutlined />}
                    style={{ backgroundColor: '#f0fdf4', color: 'var(--color-success)', flexShrink: 0 }}
                  />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <Text strong style={{ fontSize: 15, color: 'var(--color-text-primary)' }}>{t.name}</Text>
                      <Tag
                        style={{
                          fontSize: 11,
                          borderRadius: 6,
                          margin: 0,
                          background: t.risk_level === 'high' ? '#fef2f2' : t.risk_level === 'medium' ? '#fffbeb' : '#f0fdf4',
                          color: t.risk_level === 'high' ? 'var(--color-error)' : t.risk_level === 'medium' ? 'var(--color-warning)' : 'var(--color-success)',
                          border: 'none',
                        }}
                      >
                        {t.risk_level}
                      </Tag>
                    </div>
                    <Text style={{ fontSize: 13, color: 'var(--color-text-secondary)', display: 'block', marginBottom: 6 }}>
                      {t.description}
                    </Text>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
                      <Text style={{ fontSize: 12, color: 'var(--color-text-muted)', fontFamily: 'monospace' }}>
                        {(t.start_url || '').slice(0, 50)}
                      </Text>
                      <Text style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
                        Max steps: {t.max_steps}
                      </Text>
                      <Text
                        style={{
                          fontSize: 12,
                          color: t.destructive_action_allowed ? 'var(--color-warning)' : 'var(--color-text-muted)',
                        }}
                      >
                        {t.destructive_action_allowed ? '⚠ Destructive allowed' : '🔒 Destructive blocked'}
                      </Text>
                    </div>
                  </div>
                </div>
                <Space>
                  <Tooltip title="View Detail">
                    <Button
                      size="small"
                      type="link"
                      icon={<EyeOutlined />}
                      onClick={() => setDetailItem(t)}
                    >
                      View
                    </Button>
                  </Tooltip>
                  <Button size="small" type="link" onClick={() => { setEditItem(t); setModalOpen(true); }}>
                    Edit
                  </Button>
                  <Button
                    size="small"
                    type="link"
                    danger
                    onClick={() => {
                      Modal.confirm({
                        title: 'Delete Task',
                        content: `Delete "${t.name}"? This cannot be undone.`,
                        okText: 'Delete',
                        okButtonProps: { danger: true },
                        onOk: () => deleteTask.mutate(t.id),
                      });
                    }}
                  >
                    Delete
                  </Button>
                </Space>
              </div>
            </Card>
          ))}
        </div>
      )}

      <TaskForm
        open={modalOpen}
        editItem={editItem}
        onClose={() => { setModalOpen(false); setEditItem(null); }}
      />

      <EntityDetailDrawer
        entity={detailItem}
        type="task"
        open={!!detailItem}
        onClose={() => setDetailItem(null)}
      />
    </div>
  );
}
