import { Card, Typography, Button, Descriptions, Tag, Space, Divider } from 'antd';
import { ArrowLeftOutlined, EditOutlined, DeleteOutlined, SearchOutlined } from '@ant-design/icons';
import { useState } from 'react';
import { useNavigate, useParams } from 'react-router';
import { useKnowledgeItems } from '../hooks/useKnowledge';
import { useDeleteKnowledgeItem } from '../hooks/useKnowledge';
import KnowledgeForm from '../components/entities/forms/KnowledgeForm';
import dayjs from 'dayjs';
import { AppEmpty, AppLoading } from '../components/feedback/AppFeedback';

const { Title, Text, Paragraph } = Typography;

export default function KnowledgeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: items, isLoading } = useKnowledgeItems();
  const deleteItem = useDeleteKnowledgeItem();
  const [editOpen, setEditOpen] = useState(false);

  const item = items?.find(k => k.id === id);

  if (isLoading) {
    return <AppLoading tip="加载 Knowledge 详情…" minHeight={260} />;
  }

  if (!item) {
    return (
      <AppEmpty
        title="Knowledge Item Not Found"
        description="The knowledge item you are looking for does not exist."
        action={
          <Button type="primary" onClick={() => navigate('/entities')}>
            Back to Entities
          </Button>
        }
      />
    );
  }

  const isProductKnowledge = item.source_type === 'product_knowledge';

  const handleDelete = () => {
    deleteItem.mutate(id!, {
      onSuccess: () => navigate('/entities'),
    });
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/entities')}
        />
        <Title level={2} className="page-title">
          {item.title}
        </Title>
        <Tag color={isProductKnowledge ? 'blue' : 'orange'}>
          {isProductKnowledge ? '📘 Product Knowledge' : '⚠️ Failure Case'}
        </Tag>
      </div>

      <div className="app-grid-2col-wide">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          <Card className="demo-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
              <Text style={{ fontSize: 16, fontWeight: 600, color: 'var(--geist-foreground)' }}>
                Knowledge Details
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
              <Descriptions.Item label="Title">{item.title}</Descriptions.Item>
              <Descriptions.Item label="Source Type">
                <Tag color={isProductKnowledge ? 'blue' : 'orange'}>
                  {isProductKnowledge ? 'Product Knowledge' : 'Failure Case'}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Content">
                <Paragraph style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{item.content}</Paragraph>
              </Descriptions.Item>
              <Descriptions.Item label="Keywords">
                <Space size="small" wrap>
                  {(item.keywords || []).map((kw, i) => (
                    <Tag key={i}>{kw}</Tag>
                  ))}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="Source Ref">
                {item.source_ref ? (
                  <Text code copyable>{item.source_ref}</Text>
                ) : '—'}
              </Descriptions.Item>
            </Descriptions>
            <Divider style={{ margin: '16px 0' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--geist-foreground-tertiary)' }}>
              <span>Created: {dayjs(item.created_at).format('YYYY-MM-DD HH:mm')}</span>
              <span>Updated: {dayjs(item.updated_at).format('YYYY-MM-DD HH:mm')}</span>
            </div>
          </Card>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          <Card className="demo-card">
            <Text style={{ fontSize: 16, fontWeight: 600, color: 'var(--geist-foreground)', display: 'block', marginBottom: 16 }}>
              Quick Actions
            </Text>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <Button
                icon={<SearchOutlined />}
                onClick={() => navigate('/entities')}
                block
              >
                View All Knowledge
              </Button>
              <Button
                icon={<EditOutlined />}
                onClick={() => setEditOpen(true)}
                block
              >
                Edit Item
              </Button>
            </div>
          </Card>

          <Card className="demo-card">
            <Text style={{ fontSize: 16, fontWeight: 600, color: 'var(--geist-foreground)', display: 'block', marginBottom: 16 }}>
              Type Information
            </Text>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div>
                <Text style={{ fontSize: 12, color: 'var(--geist-foreground-tertiary)', display: 'block', marginBottom: 2 }}>Type</Text>
                <Text style={{ fontSize: 16, fontWeight: 600 }}>
                  {isProductKnowledge ? '📘 Product Knowledge' : '⚠️ Failure Case'}
                </Text>
              </div>
              <div>
                <Text style={{ fontSize: 12, color: 'var(--geist-foreground-tertiary)', display: 'block', marginBottom: 2 }}>Keywords</Text>
                <Text style={{ fontSize: 16, fontWeight: 600 }}>{item.keywords?.length || 0}</Text>
              </div>
            </div>
          </Card>
        </div>
      </div>

      <KnowledgeForm
        open={editOpen}
        editItem={item}
        onClose={() => setEditOpen(false)}
      />
    </div>
  );
}
