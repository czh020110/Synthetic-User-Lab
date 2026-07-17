import { Layout, Menu, Button, Drawer, Grid } from 'antd';
import {
  DashboardOutlined,
  TeamOutlined,
  PlayCircleOutlined,
  RocketOutlined,
  QuestionCircleOutlined,
  SettingOutlined,
  ToolOutlined,
  MenuOutlined,
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router';
import { useTranslation } from 'react-i18next';
import { useState } from 'react';

const { Sider, Content } = Layout;
const { useBreakpoint } = Grid;

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();
  const screens = useBreakpoint();
  const isMobile = !screens.md;
  const [drawerOpen, setDrawerOpen] = useState(false);

  const menuItems = [
    { key: '/', icon: <DashboardOutlined />, label: t('nav.dashboard') },
    { key: '/entities', icon: <TeamOutlined />, label: t('nav.entities') },
    { key: '/runs/new', icon: <RocketOutlined />, label: t('nav.startRun') },
    { key: '/system', icon: <ToolOutlined />, label: t('nav.systemConfig') },
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
  if (selectedKey.startsWith('/system')) {
    selectedKey = '/system';
  }
  if (selectedKey.startsWith('/help')) {
    selectedKey = '/help';
  }

  const handleNavigate = (key: string) => {
    navigate(key);
    setDrawerOpen(false);
  };

  const logo = (
    <div className="app-logo">
      <RocketOutlined className="logo-icon" />
      <span className="logo-text">Synthetic User Lab</span>
    </div>
  );

  const menu = (
    <Menu
      theme="dark"
      mode="inline"
      selectedKeys={[selectedKey]}
      items={menuItems}
      onClick={({ key }) => handleNavigate(key)}
      style={{ borderRight: 'none', paddingTop: 8 }}
    />
  );

  const bottomActions = (
    <div className="app-sider-bottom">
      <Button
        type="primary"
        icon={<PlayCircleOutlined />}
        block
        onClick={() => handleNavigate('/runs/new')}
      >
        {t('nav.startRun')}
      </Button>
      <div className="app-sider-bottom-row">
        <Button icon={<SettingOutlined />} onClick={() => handleNavigate('/settings')} ghost>
          {t('nav.settings')}
        </Button>
        <Button icon={<QuestionCircleOutlined />} onClick={() => handleNavigate('/help')} ghost>
          {t('nav.help')}
        </Button>
      </div>
    </div>
  );

  // Mobile: 顶部汉堡 + 抽屉侧边栏，内容区占满宽度
  if (isMobile) {
    return (
      <div className="app-layout app-layout-mobile">
        <header className="app-mobile-header">
          <Button type="text" icon={<MenuOutlined />} onClick={() => setDrawerOpen(true)} />
          {logo}
        </header>
        <Drawer
          placement="left"
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          width={260}
          className="app-mobile-drawer"
          styles={{ body: { padding: 0 } }}
        >
          <div className="app-sider app-sider-drawer">
            {logo}
            {menu}
            {bottomActions}
          </div>
        </Drawer>
        <div className="app-content-wrapper app-content-wrapper-mobile">
          <Content className="app-content">
            <Outlet />
          </Content>
        </div>
      </div>
    );
  }

  return (
    <div className="app-layout">
      <Sider className="app-sider" width={240} theme="dark">
        {logo}
        {menu}
        {bottomActions}
      </Sider>
      <div className="app-content-wrapper">
        <Content className="app-content">
          <Outlet />
        </Content>
      </div>
    </div>
  );
}
