import { Layout, Menu, Button } from 'antd';
import {
  DashboardOutlined,
  TeamOutlined,
  PlayCircleOutlined,
  RocketOutlined,
  QuestionCircleOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router';
import { useTranslation } from 'react-i18next';
import { useFrontendSettings } from '../../hooks/useFrontendSettings';
import { resolveThemeMode } from '../../theme';

const { Sider, Content } = Layout;

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();
  const { data: settings } = useFrontendSettings();
  const isDark = resolveThemeMode(settings?.theme ?? 'light') === 'dark';

  const menuItems = [
    { key: '/', icon: <DashboardOutlined />, label: t('nav.dashboard') },
    { key: '/entities', icon: <TeamOutlined />, label: t('nav.entities') },
    { key: '/runs/new', icon: <RocketOutlined />, label: t('nav.startRun') },
  ];

  // Determine selected key based on current path
  let selectedKey = location.pathname;
  if (selectedKey.startsWith('/runs/compare')) {
    selectedKey = '/runs/new';
  } else if (selectedKey.startsWith('/runs/') && selectedKey !== '/runs/new') {
    selectedKey = '/';
  }
  if (selectedKey.startsWith('/entities/')) {
    selectedKey = '/entities';
  }
  if (selectedKey.startsWith('/settings')) {
    selectedKey = '/settings';
  }
  if (selectedKey.startsWith('/help')) {
    selectedKey = '/help';
  }

  return (
    <div className="app-layout">
      <Sider
        className="app-sider"
        width={220}
        theme={isDark ? 'dark' : 'light'}
      >
        <div className="app-logo">
          <RocketOutlined className="logo-icon" />
          <span className="logo-text">Synthetic User Lab</span>
        </div>
        <Menu
          theme="light"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ borderRight: 'none', paddingTop: 8 }}
        />

        {/* Bottom Actions */}
        <div style={{
          position: 'absolute',
          bottom: 16,
          left: 16,
          right: 16,
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
        }}>
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            block
            className="btn-primary-gradient"
            onClick={() => navigate('/runs/new')}
            style={{ height: 40 }}
          >
            {t('nav.startRun')}
          </Button>
          <div style={{ display: 'flex', gap: 8 }}>
            <Button
              icon={<UserOutlined />}
              onClick={() => navigate('/settings')}
              style={{ flex: 1, height: 36 }}
            >
              {t('nav.settings')}
            </Button>
            <Button
              icon={<QuestionCircleOutlined />}
              onClick={() => navigate('/help')}
              style={{ flex: 1, height: 36 }}
            >
              {t('nav.help')}
            </Button>
          </div>
        </div>
      </Sider>
      <div className="app-content-wrapper">
        <Content className="app-content">
          <Outlet />
        </Content>
      </div>
    </div>
  );
}
