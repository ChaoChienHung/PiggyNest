import { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { RateProvider } from './context/RateProvider';
import { ThemeProvider } from './context/ThemeContext';
import { ProtectedRoute } from './components/ProtectedRoute';

const Login = lazy(() => import('./pages/Login').then(m => ({ default: m.Login })));
const Register = lazy(() => import('./pages/Register').then(m => ({ default: m.Register })));
const AccountRecovery = lazy(() => import('./pages/AccountRecovery').then(m => ({ default: m.AccountRecovery })));
const Dashboard = lazy(() => import('./pages/Dashboard').then(m => ({ default: m.Dashboard })));
const PiggyBankView = lazy(() => import('./pages/PiggyBankView').then(m => ({ default: m.PiggyBankView })));
const SettingsDialog = lazy(() => import('./components/SettingsDialog').then(m => ({ default: m.SettingsDialog })));
const Reports = lazy(() => import('./pages/Reports').then(m => ({ default: m.Reports })));
const Analysis = lazy(() => import('./pages/Analysis').then(m => ({ default: m.Analysis })));

const RouteFallback = () => (
  <div className="container" style={{ textAlign: 'center', marginTop: '4rem' }}>
    <h2 style={{ color: 'var(--text-secondary)' }}>Loading PiggyNest...</h2>
  </div>
);

const SettingsRoute = () => {
  const navigate = useNavigate();
  return <><Dashboard /><SettingsDialog onClose={() => navigate('/')} /></>;
};

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AuthProvider>
          <RateProvider>
            <Suspense fallback={<RouteFallback />}>
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
                  <Route path="/analysis" element={<Analysis />} />
                </Route>

                {/* Fallback */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Suspense>
          </RateProvider>
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
