import { Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  TeamOutlined,
  PlayCircleOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router';

const { Sider, Content } = Layout;

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: 'Dashboard' },
  { key: '/entities', icon: <TeamOutlined />, label: 'Entities' },
  { key: '/runs/new', icon: <PlayCircleOutlined />, label: 'Start Run' },
];

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();

  let selectedKey = location.pathname;
  if (selectedKey.startsWith('/runs/') && selectedKey !== '/runs/new') {
    selectedKey = '/runs/new';
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
          <RobotOutlined className="logo-icon" />
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
      </Sider>
      <div className="app-content-wrapper">
        <Content className="app-content">
          <Outlet />
        </Content>
      </div>
    </div>
  );
}
