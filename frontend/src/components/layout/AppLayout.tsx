import { Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  TeamOutlined,
  PlayCircleOutlined,
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

  // 计算 selectedKeys：精确匹配 / 或 /entities，/runs/* 匹配 /runs/new
  let selectedKey = location.pathname;
  if (selectedKey.startsWith('/runs/') && selectedKey !== '/runs/new') {
    selectedKey = '/runs/new';
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={200} theme="light">
        <div style={{ padding: '16px', fontSize: 16, fontWeight: 600, textAlign: 'center' }}>
          Synthetic User Lab
        </div>
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Content style={{ padding: '24px', background: '#fff', minHeight: 360 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
