import { Tabs, Typography, Breadcrumb, Input } from 'antd';
import { UserOutlined, FileTextOutlined, BookOutlined, SearchOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router';
import { useState } from 'react';
import PersonaList from '../components/entities/PersonaList';
import TaskList from '../components/entities/TaskList';
import KnowledgeList from '../components/entities/KnowledgeList';

const { Title, Text } = Typography;

export default function EntitiesPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');

  return (
    <div>
      {/* Breadcrumb */}
      <Breadcrumb
        style={{ marginBottom: 16 }}
        items={[
          { title: <span style={{ cursor: 'pointer' }} onClick={() => navigate('/')}>Dashboard</span> },
          { title: 'Entities' },
        ]}
      />

      <div className="page-header" style={{ marginBottom: 24 }}>
        <Title level={1} style={{ margin: 0, fontSize: 24, fontWeight: 700, color: 'var(--color-text-primary)' }}>
          Entities
        </Title>
        <Text style={{ fontSize: 14, color: 'var(--color-text-muted)', marginTop: 4, display: 'block' }}>
          管理 Personas、Tasks 和 Knowledge Items
        </Text>
      </div>

      <Tabs
        defaultActiveKey="personas"
        items={[
          {
            key: 'personas',
            label: (
              <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <UserOutlined /> Personas
              </span>
            ),
            children: <PersonaList search={search} />,
          },
          {
            key: 'tasks',
            label: (
              <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <FileTextOutlined /> Tasks
              </span>
            ),
            children: <TaskList search={search} />,
          },
          {
            key: 'knowledge',
            label: (
              <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <BookOutlined /> Knowledge
              </span>
            ),
            children: <KnowledgeList search={search} />,
          },
        ]}
        tabBarExtraContent={
          <Input
            placeholder="Search entities..."
            prefix={<SearchOutlined style={{ color: 'var(--color-text-muted)' }} />}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: 240, borderRadius: 8 }}
            allowClear
          />
        }
        style={{
          background: 'var(--color-card)',
          borderRadius: 12,
          border: '1px solid var(--color-border)',
          padding: '20px 24px 24px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02)',
        }}
      />
    </div>
  );
}
