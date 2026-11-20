import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import { authApi } from '../api/auth';
import { getApiError } from '../api/client';
import { LogIn, Moon, Sun } from 'lucide-react';
import { PiggyAnimation } from '../components/PiggyCartoon';
import { useTheme } from '../context/ThemeContext';

export const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const { login } = useAuth();
    const { theme, toggleTheme } = useTheme();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            const data = await authApi.login(email, password);
            localStorage.setItem('piggy_token', data.access_token);
            const user = await authApi.testToken();
            login(data.access_token, user);
            navigate('/');
        } catch (err: unknown) {
            setError(getApiError(err, 'Failed to login. Please check your credentials.'));
            localStorage.removeItem('piggy_token');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="auth-page-wrapper">
            <button
                type="button"
                className="btn btn-secondary auth-theme-toggle"
                onClick={toggleTheme}
                aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
                title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            >
                {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <div className="split-screen-card">
                {/* Left Side: Gorgeous Cartoon Animation Panel (Refactored) */}
                <PiggyAnimation 
                    title="PiggyNest" 
                    subtitle="Save your gold coins, build up your nests, and grow your wealth in the cutest way!" 
                />

                {/* Right Side: Clean Modern Form */}
                <div className="split-screen-right">
                    <div className="text-center mb-6">
                        <div 
                            style={{ 
                                display: 'inline-flex', 
                                alignItems: 'center', 
                                justifyContent: 'center', 
                                width: '52px', 
                                height: '52px', 
                                borderRadius: '50%',
                                backgroundColor: 'var(--accent-light)', 
                                color: 'var(--accent-primary)',
                                marginBottom: '0.75rem'
                            }}
                        >
                            <LogIn size={24} />
                        </div>
                        <h1 className="text-2xl font-bold" style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>Welcome Back</h1>
                        <p className="text-muted text-sm font-semibold">Sign in to your PiggyNest</p>
                    </div>

                    {error && (
                        <div 
                            className="text-xs text-center font-semibold animate-fade-in"
                            style={{ 
                                color: 'var(--danger)',
                                marginBottom: '1.25rem'
                            }}
                        >
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="flex flex-col gap-3.5">
                        <div>
                            <label className="block text-xs font-semibold mb-2" style={{ color: 'var(--text-secondary)' }}>Email Address</label>
                            <input
                                type="email"
                                required
                                className="input-field"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="you@example.com"
                                style={{ padding: '0.75rem 1rem' }}
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-semibold mb-2" style={{ color: 'var(--text-secondary)' }}>Password</label>
                            <input
                                type="password"
                                required
                                className="input-field"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                style={{ padding: '0.75rem 1rem' }}
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="btn btn-primary w-full"
                            style={{ marginTop: '1.75rem', padding: '0.75rem 1.25rem', borderRadius: '14px' }}
                        >
                            {isLoading ? 'Signing in...' : 'Sign In'}
                        </button>
                    </form>

                    <div className="flex justify-center gap-4 text-xs font-semibold" style={{ marginTop: '1rem', color: 'var(--accent-primary)' }}>
                        <Link to="/recover-username">Forgot username?</Link>
                        <Link to="/reset-password">Forgot password?</Link>
                    </div>

                    <p className="text-center text-xs font-semibold" style={{ marginTop: '1.75rem', color: 'var(--text-secondary)' }}>
                        Don't have an account?{' '}
                        <Link to="/register" className="font-bold" style={{ color: 'var(--accent-primary)', textDecoration: 'underline' }}>
                            Create account
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
};
