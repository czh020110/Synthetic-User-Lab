import { BrowserRouter, Routes, Route } from 'react-router';
import dayjs from 'dayjs';
import './i18n';
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
import SystemConfigPage from './pages/SystemConfigPage';
import HelpPage from './pages/HelpPage';
import NotFoundPage from './pages/NotFoundPage';
import AppProviders from './providers/AppProviders';

dayjs.locale('zh-cn');

function App() {
  return (
    <AppProviders>
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
            <Route path="/system" element={<SystemConfigPage />} />
            <Route path="/help" element={<HelpPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AppProviders>
  );
}

export default App;
