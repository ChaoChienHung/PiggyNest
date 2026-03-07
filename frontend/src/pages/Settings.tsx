import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../api/auth';
import { ArrowLeft, User, AlertTriangle } from 'lucide-react';

export const Settings = () => {
    const { user, logout } = useAuth();

    const [username, setUsername] = useState(user?.username || '');
    const [isUpdating, setIsUpdating] = useState(false);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');

    const handleUpdate = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsUpdating(true);
        setMessage('');
        setError('');

        try {
            await authApi.updateProfile(username);
            setMessage('Profile updated successfully! Refresh to see changes across the app.');
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || 'Failed to update profile');
        } finally {
            setIsUpdating(false);
        }
    };

    const handleDeleteAccount = async () => {
        const confirmMsg = "Are you absolutely sure you want to delete your entire PiggyNest account? This will permanently delete all your PiggyBanks, Transactions, and Categories. This action cannot be undone.";
        if (window.confirm(confirmMsg)) {
            try {
                await authApi.deleteAccount();
                alert('Your account has been successfully deleted. We are sorry to see you go!');
                logout();
            } catch (err) {
                console.error(err);
                alert('Failed to delete account.');
            }
        }
    };

    return (
        <div className="container py-8 animate-fade-in max-w-2xl">
            <Link to="/" className="inline-flex items-center text-muted hover:text-text-primary transition-colors mb-6">
                <ArrowLeft size={16} className="mr-2" /> Back to Dashboard
            </Link>

            <header className="mb-10">
                <h1 className="text-3xl font-bold">Account Settings</h1>
                <p className="text-muted mt-1">Manage your profile and account preferences</p>
            </header>

            <div className="glass-panel p-8 mb-8">
                <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                    <User size={20} className="text-accent-primary" /> Profile Settings
                </h2>

                {message && <div className="p-3 mb-4 text-sm text-success bg-success bg-opacity-10 border border-success border-opacity-20 rounded">{message}</div>}
                {error && <div className="p-3 mb-4 text-sm text-danger bg-danger bg-opacity-10 border border-danger border-opacity-20 rounded">{error}</div>}

                <form onSubmit={handleUpdate} className="flex flex-col gap-4">
                    <div>
                        <label className="block text-sm font-medium text-text-secondary mb-1">Email</label>
                        <input
                            type="email"
                            disabled
                            className="input-field opacity-50 cursor-not-allowed"
                            value={user?.email || ''}
                        />
                        <p className="text-xs text-muted mt-1">Email addresses cannot be changed currently.</p>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-text-secondary mb-1">Username</label>
                        <input
                            type="text"
                            required
                            className="input-field"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                        />
                    </div>

                    <div className="pt-2">
                        <button
                            type="submit"
                            disabled={isUpdating || username === user?.username}
                            className="btn btn-primary"
                        >
                            {isUpdating ? 'Saving...' : 'Save Changes'}
                        </button>
                    </div>
                </form>
            </div>

            <div className="glass-panel p-8 border border-danger border-opacity-30 border-t-4 border-t-danger">
                <h2 className="text-xl font-semibold mb-2 flex items-center gap-2 text-danger">
                    <AlertTriangle size={20} /> Danger Zone
                </h2>
                <p className="text-text-secondary text-sm mb-6">
                    Deleting your account will permanently eradicate all data associated with it, including PiggyBanks, savings, transactions, and categories.
                </p>
                <button
                    onClick={handleDeleteAccount}
                    className="btn bg-danger hover:bg-red-600 text-white border-0"
                >
                    Delete Account Permanently
                </button>
            </div>
        </div>
    );
};
