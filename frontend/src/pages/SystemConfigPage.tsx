import {
  Typography,
  Card,
  Tabs,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  Tag,
  Popconfirm,
  message,
  Alert,
} from 'antd';
import { ArrowLeftOutlined, PlusOutlined, EditOutlined, DeleteOutlined, StarFilled } from '@ant-design/icons';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import { useTranslation } from 'react-i18next';
import type { ColumnsType } from 'antd/es/table';
import type { ModelPreset, ModelPresetCreate } from '../types/system';
import {
  useModelPresets,
  useCreateModelPreset,
  useUpdateModelPreset,
  useDeleteModelPreset,
  useSetDefaultModelPreset,
  useGuardConfig,
  useUpdateGuardConfig,
} from '../hooks/useSystemConfig';
import { AppErrorState, AppLoading } from '../components/feedback/AppFeedback';
import { getErrorMessage } from '../lib/api-error';

const { Title, Text } = Typography;


function maskApiKey(key: string): string {
  if (!key) return '';
  if (key.length <= 8) return '••••';
  return `${key.slice(0, 4)}••••${key.slice(-4)}`;
}

export default function SystemConfigPage() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const presetsQuery = useModelPresets();
  const guardQuery = useGuardConfig();
  const createPreset = useCreateModelPreset();
  const updatePreset = useUpdateModelPreset();
  const deletePreset = useDeleteModelPreset();
  const setDefault = useSetDefaultModelPreset();
  const updateGuard = useUpdateGuardConfig();

  const [modalOpen, setModalOpen] = useState(false);
  const [editItem, setEditItem] = useState<ModelPreset | null>(null);
  const [form] = Form.useForm();
  const [guardForm] = Form.useForm();
  const [guardDirty, setGuardDirty] = useState(false);

  useEffect(() => {
    if (guardQuery.data) {
      guardForm.setFieldsValue({
        destructive_keywords: guardQuery.data.destructive_keywords,
        sensitive_keywords: guardQuery.data.sensitive_keywords,
      });
      setGuardDirty(false);
    }
  }, [guardQuery.data, guardForm]);

  const openCreate = () => {
    setEditItem(null);
    form.resetFields();
    form.setFieldsValue({ provider: 'openai', is_default: false });
    setModalOpen(true);
  };

  const openEdit = (preset: ModelPreset) => {
    setEditItem(preset);
    form.setFieldsValue({
      name: preset.name,
      provider: preset.provider,
      base_url: preset.base_url,
      model_name: preset.model_name,
      fast_model_name: preset.fast_model_name,
      is_default: preset.is_default,
      api_key: '', // 编辑时不回填，留空表示保持不变
    });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const isEdit = !!editItem;
      // 编辑时 api_key 留空表示不更新
      const apiKey = values.api_key || undefined;
      if (isEdit && editItem) {
        await updatePreset.mutateAsync({
          id: editItem.id,
          data: {
            name: values.name,
            provider: values.provider,
            base_url: values.base_url,
            model_name: values.model_name,
            fast_model_name: values.fast_model_name,
            api_key: apiKey,
          },
        });
        // is_default 切换单独走 setDefault 接口保证互斥
        if (values.is_default && !editItem.is_default) {
          await setDefault.mutateAsync(editItem.id);
        }
        message.success(t('system.presetUpdated'));
      } else {
        const payload: ModelPresetCreate = {
          name: values.name,
          provider: values.provider,
          base_url: values.base_url,
          model_name: values.model_name,
          fast_model_name: values.fast_model_name,
          api_key: values.api_key,
          is_default: values.is_default,
        };
        await createPreset.mutateAsync(payload);
        message.success(t('system.presetCreated'));
      }
      setModalOpen(false);
    } catch (error) {
      if ((error as { errorFields?: unknown }).errorFields) return; // 表单校验错误，不弹 toast
      message.error(getErrorMessage(error, t('common.retryLater')));
    }
  };

  const handleDelete = async (preset: ModelPreset) => {
    try {
      await deletePreset.mutateAsync(preset.id);
      message.success(t('system.presetDeleted'));
    } catch (error) {
      message.error(getErrorMessage(error, t('common.retryLater')));
    }
  };

  const handleSetDefault = async (preset: ModelPreset) => {
    try {
      await setDefault.mutateAsync(preset.id);
      message.success(t('system.defaultSet'));
    } catch (error) {
      message.error(getErrorMessage(error, t('common.retryLater')));
    }
  };

  const handleSaveGuard = async () => {
    try {
      const values = await guardForm.validateFields();
      await updateGuard.mutateAsync({
        destructive_keywords: values.destructive_keywords,
        sensitive_keywords: values.sensitive_keywords,
      });
      setGuardDirty(false);
      message.success(t('system.guardSaved'));
    } catch (error) {
      if ((error as { errorFields?: unknown }).errorFields) return;
      message.error(getErrorMessage(error, t('common.retryLater')));
    }
  };

  const columns: ColumnsType<ModelPreset> = [
    { title: t('system.presetName'), dataIndex: 'name', key: 'name' },
    { title: t('system.provider'), dataIndex: 'provider', key: 'provider' },
    { title: t('system.modelName'), dataIndex: 'model_name', key: 'model_name' },
    {
      title: t('system.apiKey'),
      dataIndex: 'api_key',
      key: 'api_key',
      render: (key: string) => (key ? maskApiKey(key) : <Text type="secondary">{t('system.notConfigured')}</Text>),
    },
    {
      title: t('system.default'),
      dataIndex: 'is_default',
      key: 'is_default',
      render: (isDefault: boolean) => (isDefault ? <Tag color="green">{t('system.defaultTag')}</Tag> : null),
    },
    {
      title: t('system.actions'),
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(record)}>
            {t('common.edit')}
          </Button>
          {!record.is_default && (
            <Button size="small" icon={<StarFilled />} onClick={() => handleSetDefault(record)}>
              {t('system.set_default')}
            </Button>
          )}
          <Popconfirm
            title={t('system.confirmDelete')}
            onConfirm={() => handleDelete(record)}
            disabled={record.is_default}
          >
            <Button size="small" danger icon={<DeleteOutlined />} disabled={record.is_default}>
              {t('common.delete')}
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  if (presetsQuery.isLoading || guardQuery.isLoading) {
    return <AppLoading tip={t('common.loading')} minHeight={260} />;
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate('/')} />
        <Title level={1} className="page-title">
          {t('system.title')}
        </Title>
      </div>

      <Tabs
        defaultActiveKey="presets"
        items={[
          {
            key: 'presets',
            label: t('system.tabPresets'),
            children: (
              <Card className="demo-card">
                <Alert
                  type="warning"
                  showIcon
                  message={t('system.apiKeyWarning')}
                  style={{ marginBottom: 16 }}
                />
                {presetsQuery.isError ? (
                  <AppErrorState
                    title={t('system.loadFailed')}
                    description={getErrorMessage(presetsQuery.error, t('common.retryLater'))}
                    onRetry={() => presetsQuery.refetch()}
                  />
                ) : (
                  <>
                    <div style={{ marginBottom: 16 }}>
                      <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
                        {t('system.newPreset')}
                      </Button>
                    </div>
                    <Table
                      rowKey="id"
                      columns={columns}
                      dataSource={presetsQuery.data}
                      pagination={false}
                      size="middle"
                    />
                  </>
                )}
              </Card>
            ),
          },
          {
            key: 'guard',
            label: t('system.tabGuard'),
            children: (
              <Card className="demo-card">
                {guardQuery.isError ? (
                  <AppErrorState
                    title={t('system.loadFailed')}
                    description={getErrorMessage(guardQuery.error, t('common.retryLater'))}
                    onRetry={() => guardQuery.refetch()}
                  />
                ) : (
                  <Form form={guardForm} layout="vertical">
                    <Alert
                      type="info"
                      showIcon
                      message={t('system.keywordHint')}
                      style={{ marginBottom: 16 }}
                    />
                    <Form.Item
                      name="destructive_keywords"
                      label={t('system.destructiveKeywords')}
                      tooltip={t('system.destructiveTip')}
                    >
                      <Select
                        mode="tags"
                        tokenSeparators={[',', '\n']}
                        placeholder={t('system.keywordPlaceholder')}
                        onChange={() => setGuardDirty(true)}
                      />
                    </Form.Item>
                    <Form.Item
                      name="sensitive_keywords"
                      label={t('system.sensitiveKeywords')}
                      tooltip={t('system.sensitiveTip')}
                    >
                      <Select
                        mode="tags"
                        tokenSeparators={[',', '\n']}
                        placeholder={t('system.keywordPlaceholder')}
                        onChange={() => setGuardDirty(true)}
                      />
                    </Form.Item>
                    <Button
                      type="primary"
                      onClick={handleSaveGuard}
                      loading={updateGuard.isPending}
                      disabled={!guardDirty}
                    >
                      {t('common.save')}
                    </Button>
                  </Form>
                )}
              </Card>
            ),
          },
        ]}
      />

      <Modal
        title={editItem ? t('system.editPreset') : t('system.newPreset')}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={handleSubmit}
        okText={editItem ? t('common.save') : t('common.create')}
        okButtonProps={{ loading: createPreset.isPending || updatePreset.isPending || setDefault.isPending }}
        width={520}
        destroyOnClose
      >
        <Form form={form} layout="vertical" preserve={false}>
          <Form.Item
            name="name"
            label={t('system.presetName')}
            rules={[{ required: true, message: t('system.presetNameRequired') }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="provider"
            label={t('system.provider')}
            rules={[{ required: true }]}
          >
            <Select
              options={[
                { value: 'openai', label: t('system.providerOpenai') },
                { value: 'dashscope', label: t('system.providerDashscope') },
              ]}
            />
          </Form.Item>
          <Form.Item name="api_key" label={t('system.apiKey')}>
            <Input.Password placeholder={editItem ? t('system.apiKeyKeepHint') : t('system.apiKeyPlaceholder')} />
          </Form.Item>
          <Form.Item name="base_url" label={t('system.baseUrl')}>
            <Input placeholder="https://api.openai.com/v1" />
          </Form.Item>
          <Form.Item
            name="model_name"
            label={t('system.modelName')}
            rules={[{ required: true, message: t('system.modelNameRequired') }]}
          >
            <Input placeholder="gpt-4o" />
          </Form.Item>
          <Form.Item name="fast_model_name" label={t('system.fastModelName')}>
            <Input placeholder={t('system.fastModelPlaceholder')} />
          </Form.Item>
          <Form.Item name="is_default" label={t('system.default')} valuePropName="checked" tooltip={editItem?.is_default ? t('system.cannotUnsetDefault') : ''}>
            <Switch disabled={!!editItem?.is_default} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
