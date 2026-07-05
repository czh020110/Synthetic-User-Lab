import { Button, Space, Card, Typography, Modal, Tag, Avatar, Tooltip } from 'antd';
import { PlusOutlined, UserOutlined, EyeOutlined } from '@ant-design/icons';
import { useState } from 'react';
import { usePersonas, useDeletePersona } from '../../hooks/usePersonas';
import type { Persona } from '../../types/persona';
import PersonaForm from './forms/PersonaForm';
import EntityDetailDrawer from './EntityDetailDrawer';

const { Text } = Typography;

export default function PersonaList() {
  const { data: personas, isLoading, isError, refetch } = usePersonas();
  const deletePersona = useDeletePersona();
  const [modalOpen, setModalOpen] = useState(false);
  const [editItem, setEditItem] = useState<Persona | null>(null);
  const [detailItem, setDetailItem] = useState<Persona | null>(null);

  const items = personas ?? [];

  if (isError) {
    return (
      <div className="error-card">
        <div className="error-icon">⚠️</div>
        <h4 style={{ margin: '0 0 4px 0', fontWeight: 600 }}>Failed to load personas</h4>
        <p style={{ margin: '0 0 16px 0' }}>Please try again.</p>
        <Button onClick={() => refetch()}>Retry</Button>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <Text style={{ fontSize: 14, color: 'var(--color-text-muted)', fontWeight: 500 }}>
          {isLoading ? 'Loading...' : `${items.length} persona${items.length !== 1 ? 's' : ''}`}
        </Text>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => { setEditItem(null); setModalOpen(true); }}
          className="btn-primary-gradient"
          style={{ fontWeight: 500 }}
        >
          + New Persona
        </Button>
      </div>

      {items.length === 0 && !isLoading ? (
        <div className="empty-state" style={{ padding: 48 }}>
          <div className="empty-icon" style={{ fontSize: 40, marginBottom: 12 }}>👤</div>
          <h4 style={{ margin: '0 0 8px 0', fontSize: 15, fontWeight: 600, color: 'var(--color-text-primary)' }}>
            No personas yet
          </h4>
          <p style={{ margin: '0 0 16px 0', color: 'var(--color-text-muted)', fontSize: 14 }}>
            Create one to get started.
          </p>
          <Button
            type="primary"
            onClick={() => setModalOpen(true)}
            className="btn-primary-gradient"
          >
            Create Persona
          </Button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {items.map((p) => (
            <Card
              key={p.id}
              className="demo-card"
              size="small"
              style={{ borderRadius: 12, border: '1px solid var(--color-border)', padding: '0' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', padding: '16px 20px' }}>
                <div style={{ display: 'flex', gap: 12, flex: 1 }}>
                  <Avatar
                    size={40}
                    icon={<UserOutlined />}
                    style={{ backgroundColor: '#eff6ff', color: 'var(--color-primary)', flexShrink: 0 }}
                  />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <Text strong style={{ fontSize: 15, color: 'var(--color-text-primary)' }}>{p.name}</Text>
                      <Tag style={{ fontSize: 11, borderRadius: 6, margin: 0 }}>{p.skill_level}</Tag>
                    </div>
                    <Text style={{ fontSize: 13, color: 'var(--color-text-secondary)', display: 'block', marginBottom: 6 }}>
                      {p.description}
                    </Text>
                    {p.patience_level && (
                      <Text style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
                        Patience: {p.patience_level} | Risk: {p.risk_preference}
                      </Text>
                    )}
                  </div>
                </div>
                <Space>
                  <Tooltip title="View Detail">
                    <Button
                      size="small"
                      type="link"
                      icon={<EyeOutlined />}
                      onClick={() => setDetailItem(p)}
                    >
                      View
                    </Button>
                  </Tooltip>
                  <Button size="small" type="link" onClick={() => { setEditItem(p); setModalOpen(true); }}>
                    Edit
                  </Button>
                  <Button
                    size="small"
                    type="link"
                    danger
                    onClick={() => {
                      Modal.confirm({
                        title: 'Delete Persona',
                        content: `Delete "${p.name}"? This cannot be undone.`,
                        okText: 'Delete',
                        okButtonProps: { danger: true },
                        onOk: () => deletePersona.mutate(p.id),
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

      <PersonaForm
        open={modalOpen}
        editItem={editItem}
        onClose={() => { setModalOpen(false); setEditItem(null); }}
      />

      <EntityDetailDrawer
        entity={detailItem}
        type="persona"
        open={!!detailItem}
        onClose={() => setDetailItem(null)}
      />
    </div>
  );
}
