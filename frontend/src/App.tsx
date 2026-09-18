
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import MainLayout from './components/layout/MainLayout';

import LandingPage from './pages/LandingPage';
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import MainDashboard from './pages/dashboard/MainDashboard';
import ProjectList from './pages/dashboard/ProjectList';
import ProjectIntelligence from './pages/dashboard/ProjectIntelligence';
import MinistryView from './pages/dashboard/MinistryView';
import SectorView from './pages/dashboard/SectorView';
import StateView from './pages/dashboard/StateView';
import NewProjectsView from './pages/dashboard/NewProjectsView';
import AIAssistant from './pages/dashboard/AIAssistant';



function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected Dashboard Routes */}
          <Route path="/dashboard" element={<MainLayout />}>
            <Route index element={<MainDashboard />} />
            <Route path="ministry" element={<MinistryView />} />
            <Route path="sector" element={<SectorView />} />
            <Route path="state" element={<StateView />} />
            <Route path="projects" element={<ProjectList />} />
            <Route path="projects/:id" element={<ProjectIntelligence />} />
            <Route path="new-projects" element={<NewProjectsView />} />
            <Route path="ai" element={<AIAssistant />} />
            {/* Add other dashboard routes here as we build them */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Route>
          
          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
