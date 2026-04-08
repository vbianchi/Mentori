import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './components/auth/LoginPage';
import Dashboard from './components/Dashboard';
import AdminDashboard from './components/admin/AdminDashboard';
import SettingsPage from './components/settings/SettingsPage';
import { useTheme } from './hooks/useTheme';
import './index.css';

function App() {
    useTheme();
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/admin" element={<AdminDashboard />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="/" element={<Dashboard />} />
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </BrowserRouter>
    );
}

export default App;
