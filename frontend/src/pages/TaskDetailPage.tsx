import { Card, Typography, Spin, Result, Button, Descriptions, Tag, Space, Divider } from 'antd';
import { ArrowLeftOutlined, EditOutlined, DeleteOutlined, RocketOutlined, LinkOutlined } from '@ant-design/icons';
import { useState } from 'react';
import { useNavigate, useParams } from 'react-router';
import { useTasks } from '../hooks/useTasks';
import { useDeleteTask } from '../hooks/useTasks';
import TaskForm from '../components/entities/forms/TaskForm';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;

export default function TaskDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: tasks, isLoading } = useTasks();
  const deleteTask = useDeleteTask();
  const [editOpen, setEditOpen] = useState(false);

  const task = tasks?.find(t => t.id === id);

  if (isLoading) {
    return (
      <div className="loading-container">
        <Spin size="large" />
      </div>
    );
  }

  if (!task) {
    return (
      <Result
        status="404"
        title="Task Not Found"
        subTitle="The task you are looking for does not exist."
        extra={
          <Button type="primary" onClick={() => navigate('/entities')}>
            Back to Entities
          </Button>
        }
      />
    );
  }

  const handleDelete = () => {
    deleteTask.mutate(id!, {
      onSuccess: () => navigate('/entities'),
    });
  };

  const riskColors = {
    high: 'red',
    medium: 'orange',
    low: 'green',
  };

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/entities')}
          style={{ borderRadius: 8 }}
        />
        <Title level={2} style={{ margin: 0, fontSize: 24, fontWeight: 700, color: 'var(--color-text-primary)' }}>
          {task.name}
        </Title>
        <Tag color={riskColors[task.risk_level]}>{task.risk_level} risk</Tag>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24 }}>
        {/* Left Column - Main Info */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          <Card className="demo-card" style={{ borderRadius: 12, border: '1px solid var(--color-border)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
              <Text style={{ fontSize: 16, fontWeight: 600, color: 'var(--color-text-primary)' }}>
                Task Details
              </Text>
              <Space>
                <Button icon={<EditOutlined />} onClick={() => setEditOpen(true)}>
                  Edit
                </Button>
                <Button danger icon={<DeleteOutlined />} onClick={handleDelete}>
                  Delete
                </Button>
              </Space>
            </div>
            <Divider style={{ margin: '0 0 16px 0' }} />
            <Descriptions column={1} size="middle">
              <Descriptions.Item label="Name">{task.name}</Descriptions.Item>
              <Descriptions.Item label="Description">
                <Paragraph style={{ margin: 0 }}>{task.description || '—'}</Paragraph>
              </Descriptions.Item>
              <Descriptions.Item label="Start URL">
                <a href={task.start_url} target="_blank" rel="noopener noreferrer">
                  <Text code>{task.start_url}</Text>
                  <LinkOutlined style={{ marginLeft: 8 }} />
                </a>
              </Descriptions.Item>
              <Descriptions.Item label="Success Criteria">
                <Space direction="vertical" size="small">
                  {task.success_criteria?.map((c, i) => (
                    <Tag key={i} style={{ margin: 0 }}>{c}</Tag>
                  )) || '—'}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="Max Steps">{task.max_steps}</Descriptions.Item>
              <Descriptions.Item label="Risk Level">
                <Tag color={riskColors[task.risk_level]}>{task.risk_level}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Destructive Actions">
                {task.destructive_action_allowed ? (
                  <Tag color="warning">Allowed</Tag>
                ) : (
                  <Tag color="success">Blocked</Tag>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="Allowed Actions">
                <Space size="small" wrap>
                  {(task.allowed_actions || []).map((a) => (
                    <Tag key={a}>{a}</Tag>
                  ))}
                </Space>
              </Descriptions.Item>
            </Descriptions>
            <Divider style={{ margin: '16px 0' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: 'var(--color-text-muted)' }}>
              <span>Created: {dayjs(task.created_at).format('YYYY-MM-DD HH:mm')}</span>
              <span>Updated: {dayjs(task.updated_at).format('YYYY-MM-DD HH:mm')}</span>
            </div>
          </Card>
        </div>

        {/* Right Column - Stats & Actions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          <Card className="demo-card" style={{ borderRadius: 12, border: '1px solid var(--color-border)' }}>
            <Text style={{ fontSize: 16, fontWeight: 600, color: 'var(--color-text-primary)', display: 'block', marginBottom: 16 }}>
              Quick Actions
            </Text>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <Button
                type="primary"
                icon={<RocketOutlined />}
                onClick={() => navigate(`/runs/new?task_id=${id}`)}
                className="btn-primary-gradient"
                block
              >
                Start New Run
              </Button>
              <Button
                icon={<EditOutlined />}
                onClick={() => setEditOpen(true)}
                block
              >
                Edit Task
              </Button>
            </div>
          </Card>

          <Card className="demo-card" style={{ borderRadius: 12, border: '1px solid var(--color-border)' }}>
            <Text style={{ fontSize: 16, fontWeight: 600, color: 'var(--color-text-primary)', display: 'block', marginBottom: 16 }}>
              Task Configuration
            </Text>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div>
                <Text style={{ fontSize: 13, color: 'var(--color-text-muted)', display: 'block', marginBottom: 4 }}>Max Steps</Text>
                <Text style={{ fontSize: 20, fontWeight: 700, color: 'var(--color-primary)' }}>{task.max_steps}</Text>
              </div>
              <div>
                <Text style={{ fontSize: 13, color: 'var(--color-text-muted)', display: 'block', marginBottom: 4 }}>Success Criteria</Text>
                <Text style={{ fontSize: 20, fontWeight: 700 }}>{task.success_criteria?.length || 0}</Text>
              </div>
              <div>
                <Text style={{ fontSize: 13, color: 'var(--color-text-muted)', display: 'block', marginBottom: 4 }}>Allowed Actions</Text>
                <Text style={{ fontSize: 20, fontWeight: 700 }}>{task.allowed_actions?.length || 0}</Text>
              </div>
            </div>
          </Card>
        </div>
      </div>

      <TaskForm
        open={editOpen}
        editItem={task}
        onClose={() => setEditOpen(false)}
      />
    </div>
  );
}
