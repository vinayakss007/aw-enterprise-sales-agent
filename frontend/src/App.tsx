import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { ToastProvider } from './contexts/ToastContext';

// Layouts
import MainLayout from './layouts/MainLayout';
import AdminLayout from './layouts/AdminLayout';

// Pages
import HomePage from './pages/common/Home';
import LoginPage from './pages/auth/Login';
import RegisterPage from './pages/auth/Register';
import NotFoundPage from './pages/common/NotFound';

// Customer Pages
import CustomerDashboard from './pages/customer/Dashboard';
import LeadsPage from './pages/customer/Leads';
import AgentPage from './pages/customer/Agent';
import CampaignsPage from './pages/customer/Campaigns';
import KnowledgePage from './pages/customer/Knowledge';

// Admin Pages
import AdminDashboard from './pages/admin/Dashboard';
import TenantsPage from './pages/admin/Tenants';
import UsersPage from './pages/admin/Users';
import UsagePage from './pages/admin/Usage';
import AuditPage from './pages/admin/Audit';
import SettingsPage from './pages/admin/Settings';

// Components
import LoadingSpinner from './components/common/LoadingSpinner';
import ProtectedRoute from './components/common/ProtectedRoute';
import AdminRoute from './components/common/AdminRoute';

// Styles
import './styles/globals.css';
import 'tailwindcss/tailwind.css';

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    },
  },
});

// Loading component for AuthProvider
const Loading = () => (
  <div className="flex items-center justify-center min-h-screen">
    <LoadingSpinner />
  </div>
);

// Main application component
const AppContent = () => {
  const { loading } = useAuth();

  if (loading) {
    return <Loading />;
  }

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Customer routes */}
          <Route
            path="/"
            element={
              <MainLayout>
                <HomePage />
              </MainLayout>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <CustomerDashboard />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/leads"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <LeadsPage />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/agent"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <AgentPage />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/campaigns"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <CampaignsPage />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/knowledge"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <KnowledgePage />
                </MainLayout>
              </ProtectedRoute>
            }
          />

          {/* Admin routes */}
          <Route
            path="/admin"
            element={
              <AdminRoute>
                <AdminLayout>
                  <AdminDashboard />
                </AdminLayout>
              </AdminRoute>
            }
          />
          <Route
            path="/admin/tenants"
            element={
              <AdminRoute>
                <AdminLayout>
                  <TenantsPage />
                </AdminLayout>
              </AdminRoute>
            }
          />
          <Route
            path="/admin/users"
            element={
              <AdminRoute>
                <AdminLayout>
                  <UsersPage />
                </AdminLayout>
              </AdminRoute>
            }
          />
          <Route
            path="/admin/usage"
            element={
              <AdminRoute>
                <AdminLayout>
                  <UsagePage />
                </AdminLayout>
              </AdminRoute>
            }
          />
          <Route
            path="/admin/audit"
            element={
              <AdminRoute>
                <AdminLayout>
                  <AuditPage />
                </AdminLayout>
              </AdminRoute>
            }
          />
          <Route
            path="/admin/settings"
            element={
              <AdminRoute>
                <AdminLayout>
                  <SettingsPage />
                </AdminLayout>
              </AdminRoute>
            }
          />

          {/* 404 Route */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </div>
    </Router>
  );
};

// Main App component
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <ToastProvider>
          <AuthProvider>
            <AppContent />
          </AuthProvider>
        </ToastProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
