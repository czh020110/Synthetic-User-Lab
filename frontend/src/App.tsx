import { BrowserRouter, Routes, Route } from 'react-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import './styles/demo.css';

import AppLayout from './components/layout/AppLayout';
import DashboardPage from './pages/DashboardPage';
import EntitiesPage from './pages/EntitiesPage';
import PersonaDetailPage from './pages/PersonaDetailPage';
import TaskDetailPage from './pages/TaskDetailPage';
import KnowledgeDetailPage from './pages/KnowledgeDetailPage';
import StartRunPage from './pages/StartRunPage';
import CompareReportPage from './pages/CompareReportPage';
import RunDetailPage from './pages/RunDetailPage';
import ReportPage from './pages/ReportPage';
import SettingsPage from './pages/SettingsPage';
import HelpPage from './pages/HelpPage';
import NotFoundPage from './pages/NotFoundPage';

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
              <Route path="/entities/personas/:id" element={<PersonaDetailPage />} />
              <Route path="/entities/tasks/:id" element={<TaskDetailPage />} />
              <Route path="/entities/knowledge/:id" element={<KnowledgeDetailPage />} />
              <Route path="/runs/new" element={<StartRunPage />} />
              <Route path="/runs/compare" element={<CompareReportPage />} />
              <Route path="/runs/:runId" element={<RunDetailPage />} />
              <Route path="/runs/:runId/report" element={<ReportPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/help" element={<HelpPage />} />
              <Route path="*" element={<NotFoundPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </ConfigProvider>
  );
}

export default App;
