import React, { useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import { authApi } from '../api/auth';
import { ArrowLeft, User, AlertTriangle, Download, Upload, LayoutList } from 'lucide-react';
import { backupApi } from '../api/backup';
import { getApiError } from '../api/client';
import type { User as UserProfile } from '../types';
import { DATE_FORMATS, asDateFormat, formatDate, todayIsoDate } from '../utils/dates';

export const Settings = () => {
    const { user, logout, updateUser } = useAuth();

    const [username, setUsername] = useState(user?.username || '');
    const [isUpdating, setIsUpdating] = useState(false);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [backupMessage, setBackupMessage] = useState('');
    const [backupError, setBackupError] = useState('');
    const [isImporting, setIsImporting] = useState(false);
    const [isExporting, setIsExporting] = useState(false);
    const importInputRef = useRef<HTMLInputElement>(null);
    const [displayMessage, setDisplayMessage] = useState('');
    const [displayError, setDisplayError] = useState('');
    const [isSavingDisplay, setIsSavingDisplay] = useState(false);

    const saveDisplay = async (save: () => Promise<UserProfile>) => {
        setDisplayMessage('');
        setDisplayError('');
        setIsSavingDisplay(true);
        try {
            const updatedUser = await save();
            updateUser(updatedUser);
            setDisplayMessage('Display preference saved.');
        } catch (err: unknown) {
            setDisplayError(getApiError(err, 'Could not save this preference.'));
        } finally {
            setIsSavingDisplay(false);
        }
    };

    const handleExport = async () => {
        setBackupError('');
        setIsExporting(true);
        try {
            await backupApi.export();
        } catch (err) {
            console.error(err);
            setBackupError('Could not export your backup.');
        } finally {
            setIsExporting(false);
        }
    };

    const handleImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        event.target.value = '';
        if (!file) return;
        setBackupError('');
        setBackupMessage('');
        setIsImporting(true);
        try {
            const result = await backupApi.import(file);
            setBackupMessage(`Imported ${result.piggy_banks_imported} piggy banks, ${result.transactions_imported} transactions, and ${result.categories_imported} categories. Return to Dashboard to see them.`);
        } catch (err: unknown) {
            setBackupError(getApiError(err, 'Could not import this backup.'));
        } finally {
            setIsImporting(false);
        }
    };

    const handleUpdate = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsUpdating(true);
        setMessage('');
        setError('');

        try {
            const updatedUser = await authApi.updateProfile(username);
            updateUser(updatedUser);
            setMessage('Profile updated successfully!');
        } catch (err: unknown) {
            console.error(err);
            setError(getApiError(err, 'Failed to update profile'));
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
        <div className="container page-layout-container animate-fade-in max-w-2xl">
            <Link to="/" className="back-to-dashboard-link">
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

            <div className="glass-panel p-8 mb-8">
                <h2 className="text-xl font-semibold mb-2 flex items-center gap-2">
                    <LayoutList size={20} className="text-accent-primary" /> Display
                </h2>
                <p className="text-text-secondary text-sm mb-6">
                    These preferences are saved to your account and apply in the browser and the CLI.
                </p>
                {displayMessage && <p className="mb-4 text-success" role="status">{displayMessage}</p>}
                {displayError && <p className="mb-4 text-danger" role="alert">{displayError}</p>}
                <div className="settings-fields">
                    <div className="settings-field">
                        <label htmlFor="transactions-per-page" className="text-sm font-medium text-text-secondary">Transactions per page</label>
                        <select
                            id="transactions-per-page"
                            className="input-field settings-select"
                            value={user?.transactions_per_page ?? 20}
                            onChange={(e) => saveDisplay(() => authApi.updateTransactionsPerPage(Number(e.target.value)))}
                            disabled={isSavingDisplay}
                        >
                            <option value={10}>10</option>
                            <option value={20}>20</option>
                            <option value={50}>50</option>
                            <option value={0}>All</option>
                        </select>
                    </div>
                    <div className="settings-field">
                        <label htmlFor="date-format" className="text-sm font-medium text-text-secondary">Date format</label>
                        <select
                            id="date-format"
                            className="input-field settings-select"
                            value={asDateFormat(user?.date_format)}
                            onChange={(e) => saveDisplay(() => authApi.updateDateFormat(e.target.value))}
                            disabled={isSavingDisplay}
                        >
                            {DATE_FORMATS.map((format) => (
                                <option key={format} value={format}>{format}</option>
                            ))}
                        </select>
                        <p className="text-xs text-muted">
                            Example: {formatDate(todayIsoDate(), asDateFormat(user?.date_format))}. Dates are typed in this format too.
                        </p>
                    </div>
                </div>
            </div>

            <div className="glass-panel p-8 mb-8">
                <h2 className="text-xl font-semibold mb-2">Backup your Piggy Banks</h2>
                <p className="text-text-secondary text-sm mb-6">
                    Export all your piggy banks and transactions to one Excel file. Import adds the banks in a backup to this account. If a bank name already exists, the whole import is rejected; no existing data is replaced.
                </p>
                {backupMessage && <p className="mb-4 text-success" role="status">{backupMessage}</p>}
                {backupError && <p className="mb-4 text-danger" role="alert">{backupError}</p>}
                <div className="backup-actions">
                    <button type="button" className="btn btn-secondary backup-action-button" onClick={handleExport} disabled={isExporting}>
                        <Download size={18} /> {isExporting ? 'Exporting...' : 'Export Excel'}
                    </button>
                    <button
                        type="button"
                        className="btn btn-primary backup-action-button"
                        onClick={() => importInputRef.current?.click()}
                        disabled={isImporting}
                    >
                        <Upload size={18} /> {isImporting ? 'Importing...' : 'Import Excel'}
                    </button>
                    <input
                        ref={importInputRef}
                        type="file"
                        accept=".xlsx"
                        className="backup-file-input"
                        aria-label="Select an Excel backup to import"
                        onChange={handleImport}
                        disabled={isImporting}
                    />
                </div>
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
