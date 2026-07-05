import { Button, Space, Card, Typography, Tag, Modal, Avatar, Tooltip } from 'antd';
import { PlusOutlined, BookOutlined, EyeOutlined } from '@ant-design/icons';
import { useState } from 'react';
import { useNavigate } from 'react-router';
import { useKnowledgeItems, useDeleteKnowledgeItem } from '../../hooks/useKnowledge';
import KnowledgeForm from './forms/KnowledgeForm';
import type { KnowledgeItem, RetrievalSourceType } from '../../types/knowledge';

const { Text } = Typography;

const sourceTypeLabels: Record<RetrievalSourceType, { label: string; color: string }> = {
  product_knowledge: { label: 'Product Knowledge', color: 'blue' },
  failure_case: { label: 'Failure Case', color: 'orange' },
};

const sourceTypeIcons: Record<RetrievalSourceType, string> = {
  product_knowledge: '📘',
  failure_case: '⚠️',
};

export default function KnowledgeList({ search = '' }: { search?: string }) {
  const navigate = useNavigate();
  const { data: items, isLoading, isError, refetch } = useKnowledgeItems();
  const deleteItem = useDeleteKnowledgeItem();
  const [modalOpen, setModalOpen] = useState(false);
  const [editItem, setEditItem] = useState<KnowledgeItem | null>(null);
  const [activeTab, setActiveTab] = useState<RetrievalSourceType | 'all'>('all');

  const allFiltered = (items ?? []).filter((item) =>
    activeTab === 'all' || item.source_type === activeTab
  );
  const filtered = search
    ? allFiltered.filter(item =>
        item.title.toLowerCase().includes(search.toLowerCase()) ||
        item.content.toLowerCase().includes(search.toLowerCase()) ||
        (item.keywords || []).some(kw => kw.toLowerCase().includes(search.toLowerCase()))
      )
    : allFiltered;

  if (isError) {
    return (
      <div className="error-card">
        <div className="error-icon">⚠️</div>
        <h4 style={{ margin: '0 0 4px 0', fontWeight: 600 }}>Failed to load knowledge items</h4>
        <p style={{ margin: '0 0 16px 0' }}>Please try again.</p>
        <Button onClick={() => refetch()}>Retry</Button>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div style={{ display: 'flex', gap: 8 }}>
          {(['all', 'product_knowledge', 'failure_case'] as const).map((tab) => {
            const isActive = activeTab === tab;
            const count = tab === 'all'
              ? items?.length ?? 0
              : items?.filter((i) => i.source_type === tab).length ?? 0;
            return (
              <Button
                key={tab}
                size="small"
                type={isActive ? 'primary' : 'default'}
                style={{
                  borderRadius: 8,
                  fontWeight: 500,
                  fontSize: 13,
                  background: isActive ? 'var(--color-primary)' : 'transparent',
                  borderColor: isActive ? 'var(--color-primary)' : 'var(--color-border)',
                  color: isActive ? '#fff' : 'var(--color-text-secondary)',
                }}
                onClick={() => setActiveTab(tab)}
              >
                {tab === 'all' ? 'All' : sourceTypeLabels[tab].label}
                <span style={{ marginLeft: 6, fontSize: 11, opacity: 0.8 }}>{count}</span>
              </Button>
            );
          })}
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => { setEditItem(null); setModalOpen(true); }}
          className="btn-primary-gradient"
          style={{ fontWeight: 500 }}
        >
          + New Knowledge
        </Button>
      </div>

      {filtered.length === 0 && !isLoading ? (
        <div className="empty-state" style={{ padding: 48 }}>
          <div className="empty-icon" style={{ fontSize: 40, marginBottom: 12 }}>📚</div>
          <h4 style={{ margin: '0 0 8px 0', fontSize: 15, fontWeight: 600, color: 'var(--color-text-primary)' }}>
            {search ? 'No matching items' : (activeTab === 'all'
              ? 'No knowledge items yet'
              : `No ${sourceTypeLabels[activeTab as RetrievalSourceType].label.toLowerCase()} entries`)}
          </h4>
          <p style={{ margin: '0 0 16px 0', color: 'var(--color-text-muted)', fontSize: 14 }}>
            {search ? 'Try a different search term.' : 'Knowledge items power RAG retrieval for runs.'}
          </p>
          {!search && (
            <Button type="primary" onClick={() => { setEditItem(null); setModalOpen(true); }} className="btn-primary-gradient">
              Create Knowledge Item
            </Button>
          )}
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {filtered.map((item) => {
            const st = item.source_type as RetrievalSourceType;
            const stInfo = sourceTypeLabels[st];
            return (
              <Card
                key={item.id}
                className="demo-card"
                size="small"
                style={{ borderRadius: 12, border: '1px solid var(--color-border)', cursor: 'pointer' }}
                onClick={() => navigate(`/entities/knowledge/${item.id}`)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', padding: '4px' }}>
                  <div style={{ display: 'flex', gap: 12, flex: 1 }}>
                    <Avatar
                      size={40}
                      icon={<BookOutlined />}
                      style={{
                        backgroundColor: st === 'product_knowledge' ? '#eff6ff' : '#fff7ed',
                        color: st === 'product_knowledge' ? 'var(--color-primary)' : 'var(--color-warning)',
                        flexShrink: 0,
                      }}
                    />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                        <Text strong style={{ fontSize: 15, color: 'var(--color-text-primary)' }}>
                          {item.title}
                        </Text>
                        <Tag
                          color={stInfo.color}
                          style={{ fontSize: 11, borderRadius: 6, margin: 0 }}
                        >
                          {sourceTypeIcons[st]} {stInfo.label}
                        </Tag>
                      </div>
                      <Text style={{ fontSize: 13, color: 'var(--color-text-secondary)', display: 'block', marginBottom: 6 }}>
                        {item.content}
                      </Text>
                      {item.keywords && item.keywords.length > 0 && (
                        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                          {item.keywords.map((kw) => (
                            <Tag
                              key={kw}
                              style={{
                                fontSize: 11,
                                borderRadius: 6,
                                background: 'var(--color-bg)',
                                border: '1px solid var(--color-border)',
                                color: 'var(--color-text-muted)',
                              }}
                            >
                              {kw}
                            </Tag>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  <Space onClick={(e) => e.stopPropagation()}>
                    <Tooltip title="View Detail">
                      <Button
                        size="small"
                        type="link"
                        icon={<EyeOutlined />}
                        onClick={() => navigate(`/entities/knowledge/${item.id}`)}
                      >
                        View
                      </Button>
                    </Tooltip>
                    <Button size="small" type="link" onClick={() => { setEditItem(item); setModalOpen(true); }}>
                      Edit
                    </Button>
                    <Button
                      size="small"
                      type="link"
                      danger
                      onClick={() => {
                        Modal.confirm({
                          title: 'Delete Knowledge Item',
                          content: `Delete "${item.title}"? This cannot be undone.`,
                          okText: 'Delete',
                          okButtonProps: { danger: true },
                          onOk: () => deleteItem.mutate(item.id),
                        });
                      }}
                    >
                      Delete
                    </Button>
                  </Space>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      <KnowledgeForm
        open={modalOpen}
        editItem={editItem}
        onClose={() => { setModalOpen(false); setEditItem(null); }}
      />
    </div>
  );
}
