import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { RateProvider } from './context/RateProvider';
import { ProtectedRoute } from './components/ProtectedRoute';

import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { AccountRecovery } from './pages/AccountRecovery';
import { Dashboard } from './pages/Dashboard';
import { PiggyBankView } from './pages/PiggyBankView';
import { SettingsDialog } from './components/SettingsDialog';
import { Reports } from './pages/Reports';

const SettingsRoute = () => {
  const navigate = useNavigate();
  return <><Dashboard /><SettingsDialog onClose={() => navigate('/')} /></>;
};

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <RateProvider>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/recover-username" element={<AccountRecovery mode="username" />} />
          <Route path="/reset-password" element={<AccountRecovery mode="password" />} />

          {/* Protected Routes */}
          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/piggybanks/:id" element={<PiggyBankView />} />
            <Route path="/settings" element={<SettingsRoute />} />
            <Route path="/reports" element={<Reports />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        </RateProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
