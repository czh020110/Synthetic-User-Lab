import { Drawer, Descriptions, Tag, Typography, Space } from 'antd';
import type { Persona } from '../../types/persona';
import type { Task } from '../../types/task';
import type { KnowledgeItem } from '../../types/knowledge';

const { Title, Text } = Typography;

interface EntityDetailDrawerProps {
  entity: Persona | Task | KnowledgeItem | null;
  type: 'persona' | 'task' | 'knowledge' | null;
  open: boolean;
  onClose: () => void;
}

export default function EntityDetailDrawer({ entity, type, open, onClose }: EntityDetailDrawerProps) {
  if (!entity || !type) return null;

  const renderPersonaDetail = (p: Persona) => (
    <>
      <Title level={4} style={{ marginBottom: 24 }}>{p.name}</Title>
      <Descriptions bordered column={1} size="middle">
        <Descriptions.Item label="Name">{p.name}</Descriptions.Item>
        <Descriptions.Item label="Description">{p.description || '—'}</Descriptions.Item>
        <Descriptions.Item label="Skill Level">
          <Tag>{p.skill_level}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Patience Level">
          <Tag>{p.patience_level}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Risk Preference">
          <Tag>{p.risk_preference}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Created">{p.created_at}</Descriptions.Item>
        <Descriptions.Item label="Updated">{p.updated_at}</Descriptions.Item>
      </Descriptions>
    </>
  );

  const renderTaskDetail = (t: Task) => (
    <>
      <Title level={4} style={{ marginBottom: 24 }}>{t.name}</Title>
      <Descriptions bordered column={1} size="middle">
        <Descriptions.Item label="Name">{t.name}</Descriptions.Item>
        <Descriptions.Item label="Description">{t.description || '—'}</Descriptions.Item>
        <Descriptions.Item label="Start URL">
          <Text copyable style={{ fontFamily: 'monospace', fontSize: 13 }}>{t.start_url}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="Success Criteria">
          {t.success_criteria?.length > 0 ? (
            <Space direction="vertical" size="small">
              {t.success_criteria.map((c, i) => (
                <Tag key={i} style={{ margin: 0 }}>{c}</Tag>
              ))}
            </Space>
          ) : '—'}
        </Descriptions.Item>
        <Descriptions.Item label="Max Steps">{t.max_steps}</Descriptions.Item>
        <Descriptions.Item label="Risk Level">
          <Tag color={t.risk_level === 'high' ? 'error' : t.risk_level === 'medium' ? 'warning' : 'success'}>
            {t.risk_level}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Destructive Actions">
          {t.destructive_action_allowed ? (
            <Tag color="warning">Allowed</Tag>
          ) : (
            <Tag color="default">Blocked</Tag>
          )}
        </Descriptions.Item>
        <Descriptions.Item label="Allowed Actions">
          <Space size="small" wrap>
            {t.allowed_actions?.map((a) => (
              <Tag key={a} style={{ margin: 0 }}>{a}</Tag>
            )) || '—'}
          </Space>
        </Descriptions.Item>
        <Descriptions.Item label="Created">{t.created_at}</Descriptions.Item>
        <Descriptions.Item label="Updated">{t.updated_at}</Descriptions.Item>
      </Descriptions>
    </>
  );

  const renderKnowledgeDetail = (k: KnowledgeItem) => (
    <>
      <Title level={4} style={{ marginBottom: 24 }}>{k.title}</Title>
      <Descriptions bordered column={1} size="middle">
        <Descriptions.Item label="Title">{k.title}</Descriptions.Item>
        <Descriptions.Item label="Source Type">
          <Tag color={k.source_type === 'product_knowledge' ? 'blue' : 'orange'}>
            {k.source_type === 'product_knowledge' ? '📘 Product Knowledge' : '⚠️ Failure Case'}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Content">{k.content}</Descriptions.Item>
        <Descriptions.Item label="Keywords">
          <Space size="small" wrap>
            {k.keywords?.map((kw) => (
              <Tag key={kw} style={{ margin: 0 }}>{kw}</Tag>
            )) || '—'}
          </Space>
        </Descriptions.Item>
        <Descriptions.Item label="Source Ref">{k.source_ref || '—'}</Descriptions.Item>
        <Descriptions.Item label="Created">{k.created_at}</Descriptions.Item>
        <Descriptions.Item label="Updated">{k.updated_at}</Descriptions.Item>
      </Descriptions>
    </>
  );

  const titleMap = {
    persona: 'Persona Detail',
    task: 'Task Detail',
    knowledge: 'Knowledge Detail',
  };

  return (
    <Drawer
      title={type ? titleMap[type] : 'Detail'}
      placement="right"
      width={520}
      open={open}
      onClose={onClose}
    >
      {type === 'persona' && renderPersonaDetail(entity as Persona)}
      {type === 'task' && renderTaskDetail(entity as Task)}
      {type === 'knowledge' && renderKnowledgeDetail(entity as KnowledgeItem)}
    </Drawer>
  );
}
