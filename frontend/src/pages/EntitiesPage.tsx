import { Tabs, message } from 'antd';
import { UserOutlined, FileTextOutlined, BookOutlined } from '@ant-design/icons';
import PersonaList from '../components/entities/PersonaList';
import TaskList from '../components/entities/TaskList';
import KnowledgeList from '../components/entities/KnowledgeList';

export default function EntitiesPage() {
  return (
    <Tabs
      defaultActiveKey="personas"
      items={[
        {
          key: 'personas',
          label: (
            <span>
              <UserOutlined /> Personas
            </span>
          ),
          children: <PersonaList />,
        },
        {
          key: 'tasks',
          label: (
            <span>
              <FileTextOutlined /> Tasks
            </span>
          ),
          children: <TaskList />,
        },
        {
          key: 'knowledge',
          label: (
            <span>
              <BookOutlined /> Knowledge
            </span>
          ),
          children: <KnowledgeList />,
        },
      ]}
    />
  );
}
