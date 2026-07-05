import { Layout, Menu, Button } from 'antd';
import {
  DashboardOutlined,
  TeamOutlined,
  PlayCircleOutlined,
  RocketOutlined,
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

  let selectedKey = location.pathname;
  if (selectedKey.startsWith('/runs/') && selectedKey !== '/runs/new') {
    selectedKey = '/';
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
        <div style={{
          position: 'absolute',
          bottom: 16,
          left: 16,
          right: 16,
          padding: '12px',
          background: 'linear-gradient(135deg, rgba(37,99,235,0.04), rgba(37,99,235,0.08))',
          borderRadius: 12,
          border: '1px solid rgba(37,99,235,0.12)',
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
