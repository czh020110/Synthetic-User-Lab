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
      <Breadcrumb
        style={{ marginBottom: 16 }}
        items={[
          { title: <span style={{ cursor: 'pointer' }} onClick={() => navigate('/')}>Dashboard</span> },
          { title: 'Entities' },
        ]}
      />

      <div className="page-header">
        <Title level={1} className="page-title">
          Entities
        </Title>
        <Text className="page-subtitle">
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
            prefix={<SearchOutlined style={{ color: 'var(--geist-foreground-tertiary)' }} />}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: 240 }}
            allowClear
          />
        }
        style={{
          background: 'var(--geist-card-bg)',
          borderRadius: 8,
          border: '1px solid var(--geist-border)',
          padding: '16px 24px 24px',
        }}
      />
    </div>
  );
}
