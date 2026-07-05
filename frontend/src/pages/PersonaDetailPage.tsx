import { Card, Typography, Spin, Result, Button, Descriptions, Tag, Space, Divider } from 'antd';
import { ArrowLeftOutlined, EditOutlined, DeleteOutlined, PlayCircleOutlined } from '@ant-design/icons';
import { useState } from 'react';
import { useNavigate, useParams } from 'react-router';
import { usePersonas, useDeletePersona } from '../hooks/usePersonas';
import PersonaForm from '../components/entities/forms/PersonaForm';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;

export default function PersonaDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: personas, isLoading } = usePersonas();
  const deletePersona = useDeletePersona();
  const [editOpen, setEditOpen] = useState(false);

  const persona = personas?.find(p => p.id === id);

  if (isLoading) {
    return (
      <div className="loading-container">
        <Spin size="large" />
      </div>
    );
  }

  if (!persona) {
    return (
      <Result
        status="404"
        title="Persona Not Found"
        subTitle="The persona you are looking for does not exist."
        extra={
          <Button type="primary" onClick={() => navigate('/entities')}>
            Back to Entities
          </Button>
        }
      />
    );
  }

  const handleDelete = () => {
    deletePersona.mutate(id!, {
      onSuccess: () => navigate('/entities'),
    });
  };

  const handleStartRun = () => {
    navigate(`/runs/new?persona_id=${id}`);
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
          {persona.name}
        </Title>
        <Tag color="blue">{persona.skill_level}</Tag>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Left Column - Main Info */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          <Card className="demo-card" style={{ borderRadius: 12, border: '1px solid var(--color-border)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
              <Text style={{ fontSize: 16, fontWeight: 600, color: 'var(--color-text-primary)' }}>
                Persona Details
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
              <Descriptions.Item label="Name">{persona.name}</Descriptions.Item>
              <Descriptions.Item label="Description">
                <Paragraph style={{ margin: 0 }}>{persona.description || '—'}</Paragraph>
              </Descriptions.Item>
              <Descriptions.Item label="Skill Level">
                <Tag color={persona.skill_level === 'expert' ? 'green' : persona.skill_level === 'intermediate' ? 'blue' : 'orange'}>
                  {persona.skill_level}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Patience Level">
                <Tag>{persona.patience_level}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Risk Preference">
                <Tag color={persona.risk_preference === 'high' ? 'red' : persona.risk_preference === 'medium' ? 'orange' : 'green'}>
                  {persona.risk_preference}
                </Tag>
              </Descriptions.Item>
            </Descriptions>
            <Divider style={{ margin: '16px 0' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: 'var(--color-text-muted)' }}>
              <span>Created: {dayjs(persona.created_at).format('YYYY-MM-DD HH:mm')}</span>
              <span>Updated: {dayjs(persona.updated_at).format('YYYY-MM-DD HH:mm')}</span>
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
                icon={<PlayCircleOutlined />}
                onClick={handleStartRun}
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
                Edit Persona
              </Button>
            </div>
          </Card>

          <Card className="demo-card" style={{ borderRadius: 12, border: '1px solid var(--color-border)' }}>
            <Text style={{ fontSize: 16, fontWeight: 600, color: 'var(--color-text-primary)', display: 'block', marginBottom: 16 }}>
              Persona Attributes
            </Text>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div>
                <Text style={{ fontSize: 13, color: 'var(--color-text-muted)', display: 'block', marginBottom: 4 }}>Skill Level</Text>
                <Text style={{ fontSize: 18, fontWeight: 600 }}>{persona.skill_level}</Text>
              </div>
              <div>
                <Text style={{ fontSize: 13, color: 'var(--color-text-muted)', display: 'block', marginBottom: 4 }}>Patience</Text>
                <Text style={{ fontSize: 18, fontWeight: 600 }}>{persona.patience_level}</Text>
              </div>
              <div>
                <Text style={{ fontSize: 13, color: 'var(--color-text-muted)', display: 'block', marginBottom: 4 }}>Risk Preference</Text>
                <Text style={{ fontSize: 18, fontWeight: 600 }}>{persona.risk_preference}</Text>
              </div>
            </div>
          </Card>
        </div>
      </div>

      <PersonaForm
        open={editOpen}
        editItem={persona}
        onClose={() => setEditOpen(false)}
      />
    </div>
  );
}
