import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const ProtectedRoute = () => {
    const { token, isLoading } = useAuth();

    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-screen w-full">
                <div className="animate-fade-in text-muted">Loading PiggyNest...</div>
            </div>
        );
    }

    return token ? <Outlet /> : <Navigate to="/login" replace />;
};
