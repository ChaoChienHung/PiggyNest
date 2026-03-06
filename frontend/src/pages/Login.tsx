import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../api/auth';
import { LogIn } from 'lucide-react';

export const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            const data = await authApi.login(email, password);
            // After login, we need to fetch the user details to populate the context, or we can just decoded from token if needed
            // Here we just test the token to get the user
            localStorage.setItem('piggy_token', data.access_token);
            const user = await authApi.testToken();
            login(data.access_token, user);
            navigate('/');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to login');
            localStorage.removeItem('piggy_token');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex justify-center items-center min-h-screen p-4">
            <div className="glass-panel p-8 w-full max-w-md animate-fade-in">
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center p-3 rounded-full bg-accent-light text-accent-primary mb-4">
                        <LogIn size={32} />
                    </div>
                    <h1 className="text-2xl font-bold">Welcome Back</h1>
                    <p className="text-muted mt-2">Sign in to your PiggyNest</p>
                </div>

                {error && (
                    <div className="bg-danger text-white p-3 rounded-lg mb-6 text-sm text-center bg-opacity-10 border border-danger">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                    <div>
                        <label className="block text-sm font-medium text-text-secondary mb-1">Email Address</label>
                        <input
                            type="email"
                            required
                            className="input-field"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="you@example.com"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-text-secondary mb-1">Password</label>
                        <input
                            type="password"
                            required
                            className="input-field"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="••••••••"
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading}
                        className="btn btn-primary w-full mt-4"
                    >
                        {isLoading ? 'Signing in...' : 'Sign In'}
                    </button>
                </form>

                <p className="text-center mt-6 text-sm text-text-secondary">
                    Don't have an account?{' '}
                    <Link to="/register" className="text-accent-primary hover:text-accent-hover font-medium">
                        Create account
                    </Link>
                </p>
            </div>
        </div>
    );
};
