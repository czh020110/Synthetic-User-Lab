import { BrowserRouter, Routes, Route } from 'react-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';

import AppLayout from './components/layout/AppLayout';
import DashboardPage from './pages/DashboardPage';
import EntitiesPage from './pages/EntitiesPage';
import StartRunPage from './pages/StartRunPage';
import RunDetailPage from './pages/RunDetailPage';
import ReportPage from './pages/ReportPage';

dayjs.locale('zh-cn');

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            <Route element={<AppLayout />}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/entities" element={<EntitiesPage />} />
              <Route path="/runs/new" element={<StartRunPage />} />
              <Route path="/runs/:runId" element={<RunDetailPage />} />
              <Route path="/runs/:runId/report" element={<ReportPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </ConfigProvider>
  );
}

export default App;
