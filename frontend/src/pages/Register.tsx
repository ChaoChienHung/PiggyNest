import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authApi } from '../api/auth';
import { getApiError } from '../api/client';
import { UserPlus } from 'lucide-react';
import { PiggyAnimation } from '../components/PiggyCartoon';

export const Register = () => {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        setIsLoading(true);

        try {
            await authApi.register(username, email, password);
            navigate('/login');
        } catch (err: unknown) {
            setError(getApiError(err, 'Failed to create account. Email may already be taken.'));
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="auth-page-wrapper">
            <div className="split-screen-card">
                {/* Left Side: Gorgeous Cartoon Animation Panel (Refactored) */}
                <PiggyAnimation 
                    title="PiggyNest" 
                    subtitle="Save your gold coins, build up your nests, and grow your wealth in the cutest way!" 
                />

                {/* Right Side: Clean Modern Form */}
                <div className="split-screen-right">
                    <div className="text-center mb-5">
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
                            <UserPlus size={24} />
                        </div>
                        <h1 className="text-2xl font-bold" style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>Create Account</h1>
                        <p className="text-muted text-sm font-semibold">Start your savings journey with PiggyNest</p>
                    </div>

                    {error && (
                        <div 
                            className="text-xs text-center font-semibold animate-fade-in"
                            style={{ 
                                color: 'var(--danger)',
                                marginBottom: '1.25rem'
                            }}
                        >
                            ⚠️ {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
                        <div>
                            <label className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--text-secondary)' }}>Username</label>
                            <input
                                type="text"
                                required
                                className="input-field"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                placeholder="PiggyLover99"
                                style={{ padding: '0.7rem 0.95rem' }}
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--text-secondary)' }}>Email Address</label>
                            <input
                                type="email"
                                required
                                className="input-field"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="you@example.com"
                                style={{ padding: '0.7rem 0.95rem' }}
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--text-secondary)' }}>Password</label>
                            <input
                                type="password"
                                required
                                className="input-field"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                style={{ padding: '0.7rem 0.95rem' }}
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--text-secondary)' }}>Confirm Password</label>
                            <input
                                type="password"
                                required
                                className="input-field"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                placeholder="••••••••"
                                style={{ padding: '0.7rem 0.95rem' }}
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="btn btn-primary w-full"
                            style={{ marginTop: '1.75rem', padding: '0.7rem 1.25rem', borderRadius: '14px' }}
                        >
                            {isLoading ? 'Creating...' : 'Create Account 🐷'}
                        </button>
                    </form>

                    <p className="text-center text-xs font-semibold" style={{ marginTop: '1.75rem', color: 'var(--text-secondary)' }}>
                        Already have an account?{' '}
                        <Link to="/login" className="font-bold" style={{ color: 'var(--accent-primary)', textDecoration: 'underline' }}>
                            Sign in
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
};
