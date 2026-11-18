import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { Mail } from 'lucide-react';
import { authApi } from '../api/auth';
import { getApiError } from '../api/client';
import { PiggyAnimation } from '../components/PiggyCartoon';

export const AccountRecovery = ({ mode }: { mode: 'username' | 'password' }) => {
    const [email, setEmail] = useState('');
    const [code, setCode] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [codeRequested, setCodeRequested] = useState(false);
    const [completed, setCompleted] = useState(false);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');

    const request = async (event: FormEvent) => {
        event.preventDefault();
        setError('');
        setBusy(true);
        try {
            if (mode === 'username') {
                await authApi.remindUsername(email);
                setCompleted(true);
            } else {
                await authApi.requestPasswordReset(email);
                setCodeRequested(true);
            }
        } catch (err) {
            setError(getApiError(err, 'Could not request account recovery.'));
        } finally {
            setBusy(false);
        }
    };

    const confirm = async (event: FormEvent) => {
        event.preventDefault();
        setError('');
        if (password !== confirmPassword) {
            setError('Passwords do not match.');
            return;
        }
        setBusy(true);
        try {
            await authApi.confirmPasswordReset(email, code, password);
            setCompleted(true);
        } catch (err) {
            setError(getApiError(err, 'Could not reset password.'));
        } finally {
            setBusy(false);
        }
    };

    const title = mode === 'username' ? 'Forgot username?' : 'Reset password';
    return (
        <div className="auth-page-wrapper recovery-page">
            <div className={`split-screen-card ${codeRequested ? 'recovery-card-expanded' : ''}`}>
                <PiggyAnimation title="PiggyNest" subtitle="Find your way back to your nest." />
                <div className="split-screen-right">
                    <div className="text-center mb-6">
                        <div style={{ display: 'inline-flex', padding: '0.8rem', borderRadius: '16px', background: 'var(--accent-light)', color: 'var(--accent-primary)', marginBottom: '0.75rem' }}>
                            <Mail size={24} />
                        </div>
                        <h1 className="text-2xl">{title}</h1>
                        <p className="text-muted text-sm">{mode === 'username' ? 'We can email your username to your registered address.' : 'We will email a code to your registered address.'}</p>
                    </div>
                    {error && <p role="alert" className="text-center text-sm mb-4" style={{ color: 'var(--danger)' }}>{error}</p>}
                    {completed ? (
                        <p role="status" className="text-center text-sm mb-4">
                            {mode === 'username' ? 'If this email belongs to an account, a reminder will arrive shortly.' : 'Password updated. Please sign in again.'}
                        </p>
                    ) : !codeRequested ? (
                        <form onSubmit={request} className="flex flex-col gap-4">
                            <label className="text-sm font-semibold">Email address
                                <input type="email" required autoComplete="email" className="input-field mt-2" value={email} onChange={event => setEmail(event.target.value)} />
                            </label>
                            <button type="submit" className="btn btn-primary w-full" disabled={busy}>{busy ? 'Sending...' : 'Send email'}</button>
                        </form>
                    ) : (
                        <form onSubmit={confirm} className="flex flex-col gap-4">
                            <p className="text-sm text-center">If {email} belongs to an account, a code will arrive shortly. It expires in 10 minutes.</p>
                            <label className="text-sm font-semibold">8-digit code
                                <input type="text" inputMode="numeric" pattern="[0-9]{8}" required autoComplete="one-time-code" className="input-field mt-2" value={code} onChange={event => setCode(event.target.value)} />
                            </label>
                            <label className="text-sm font-semibold">New password
                                <input type="password" minLength={8} maxLength={128} required autoComplete="new-password" className="input-field mt-2" value={password} onChange={event => setPassword(event.target.value)} />
                            </label>
                            <label className="text-sm font-semibold">Confirm new password
                                <input type="password" minLength={8} maxLength={128} required autoComplete="new-password" className="input-field mt-2" value={confirmPassword} onChange={event => setConfirmPassword(event.target.value)} />
                            </label>
                            <button type="submit" className="btn btn-primary w-full" disabled={busy}>{busy ? 'Updating...' : 'Reset password'}</button>
                            <button type="button" className="text-sm font-semibold" style={{ color: 'var(--accent-primary)', background: 'none', border: 'none', cursor: 'pointer' }} onClick={() => setCodeRequested(false)}>Request another code</button>
                        </form>
                    )}
                    <p className="text-center text-sm mt-6"><Link to="/login" style={{ color: 'var(--accent-primary)' }}>Back to sign in</Link></p>
                </div>
            </div>
        </div>
    );
};
