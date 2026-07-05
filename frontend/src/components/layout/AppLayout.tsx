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

const { Sider, Content } = Layout;

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: 'Dashboard' },
  { key: '/entities', icon: <TeamOutlined />, label: 'Entities' },
  { key: '/runs/new', icon: <RocketOutlined />, label: 'Start Run' },
];

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();

  // Determine selected key based on current path
  let selectedKey = location.pathname;
  if (selectedKey.startsWith('/runs/') && selectedKey !== '/runs/new') {
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
        theme="light"
        style={{ background: '#ffffff' }}
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
            Start Formal Run
          </Button>
          <div style={{ display: 'flex', gap: 8 }}>
            <Button
              icon={<UserOutlined />}
              onClick={() => navigate('/settings')}
              style={{ flex: 1, height: 36 }}
            >
              Settings
            </Button>
            <Button
              icon={<QuestionCircleOutlined />}
              onClick={() => navigate('/help')}
              style={{ flex: 1, height: 36 }}
            >
              Help
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
