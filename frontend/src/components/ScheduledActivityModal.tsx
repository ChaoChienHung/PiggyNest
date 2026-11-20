import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import {
    Check,
    ClipboardList,
    Pause,
    PiggyBank as PiggyBankIcon,
    Play,
    Repeat,
    ShoppingCart,
    Square,
    Trash2,
    X,
} from 'lucide-react';
import { pendingApi } from '../api/pending';
import { recurringApi } from '../api/recurring';
import { getApiError } from '../api/client';
import type { PendingTransaction, RecurrenceStatus, RecurringRule } from '../types';
import { useAuth } from '../context/useAuth';
import { asDateFormat, formatDate, parseDate, todayIsoDate } from '../utils/dates';
import { formatMoney } from '../utils/money';
import { DateTextField } from './DateTextField';

interface ScheduledActivityModalProps {
    initialTab?: 'pending' | 'recurring';
    onClose: () => void;
    onChanged: () => void;
}

export const ScheduledActivityModal: React.FC<ScheduledActivityModalProps> = ({
    initialTab = 'pending',
    onClose,
    onChanged,
}) => {
    const { user } = useAuth();
    const dateFormat = asDateFormat(user?.date_format);

    const [activeTab, setActiveTab] = useState<'pending' | 'recurring'>(initialTab);
    const [pendingItems, setPendingItems] = useState<PendingTransaction[]>([]);
    const [rules, setRules] = useState<RecurringRule[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [busyId, setBusyId] = useState<number | null>(null);

    // Inline confirmation state for pending item
    const [confirmingId, setConfirmingId] = useState<number | null>(null);
    const [confirmDateText, setConfirmDateText] = useState('');
    const [confirmAmount, setConfirmAmount] = useState('');

    const loadAll = async () => {
        try {
            const [pendingList, ruleList] = await Promise.all([
                pendingApi.list('pending'),
                recurringApi.list(),
            ]);
            setPendingItems(pendingList);
            setRules(ruleList);
        } catch (err) {
            setError(getApiError(err, 'Failed to load Ledger Queue.'));
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadAll();
    }, []);

    useEffect(() => {
        const onKey = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose();
        };
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, [onClose]);

    const startConfirm = (item: PendingTransaction) => {
        setError('');
        setConfirmingId(item.id);
        setConfirmDateText(
            item.expected_date
                ? formatDate(item.expected_date, dateFormat)
                : formatDate(todayIsoDate(), dateFormat),
        );
        setConfirmAmount(String(Math.abs(item.amount)));
    };

    const handleConfirm = async (item: PendingTransaction) => {
        setError('');
        const parsedDate = parseDate(confirmDateText, dateFormat);
        if (!parsedDate) {
            setError(`Settlement date must use ${dateFormat}.`);
            return;
        }
        const numeric = Math.abs(Number(confirmAmount));
        if (!numeric || Number.isNaN(numeric)) {
            setError('Please enter a valid positive amount.');
            return;
        }
        const signed = item.amount >= 0 ? numeric : -numeric;
        setBusyId(item.id);
        try {
            await pendingApi.confirm(item.id, {
                date: `${parsedDate}T00:00:00`,
                amount: signed,
            });
            setConfirmingId(null);
            await loadAll();
            onChanged();
        } catch (err) {
            setError(getApiError(err, 'Failed to confirm pending transaction.'));
        } finally {
            setBusyId(null);
        }
    };

    const handleDeletePending = async (id: number) => {
        setError('');
        setBusyId(id);
        try {
            await pendingApi.delete(id);
            if (confirmingId === id) setConfirmingId(null);
            await loadAll();
            onChanged();
        } catch (err) {
            setError(getApiError(err, 'Failed to remove pending transaction.'));
        } finally {
            setBusyId(null);
        }
    };

    const handleRuleStatus = async (rule: RecurringRule, status: RecurrenceStatus) => {
        setError('');
        setBusyId(rule.id);
        try {
            await recurringApi.update(rule.id, { status });
            await loadAll();
            onChanged();
        } catch (err) {
            setError(getApiError(err, 'Failed to update schedule status.'));
        } finally {
            setBusyId(null);
        }
    };

    const handleDeleteRule = async (id: number) => {
        setError('');
        setBusyId(id);
        try {
            await recurringApi.delete(id);
            await loadAll();
            onChanged();
        } catch (err) {
            setError(getApiError(err, 'Failed to delete recurring schedule.'));
        } finally {
            setBusyId(null);
        }
    };

    const activeRuleCount = rules.filter((r) => r.status === 'active').length;

    return createPortal(
        <div
            className="modal-backdrop"
            role="presentation"
            onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
        >
            <div
                className="glass-panel utility-modal animate-fade-in"
                role="dialog"
                aria-modal="true"
                aria-labelledby="ledger-queue-title"
            >
                <div className="utility-modal-header">
                    <div className="flex items-center gap-3">
                        <ClipboardList size={22} className="text-accent-primary" />
                        <div>
                            <h2 id="ledger-queue-title" className="text-xl font-bold" style={{ marginBottom: 0 }}>
                                Ledger Queue
                            </h2>
                            <p className="text-xs text-muted">
                                Review pending payments and manage automatic recurring schedules.
                            </p>
                        </div>
                    </div>
                    <button
                        type="button"
                        className="btn btn-secondary utility-icon-close"
                        onClick={onClose}
                        aria-label="Close Ledger Queue"
                    >
                        <X size={18} />
                    </button>
                </div>

                <div className="utility-tabs" role="tablist" aria-label="Ledger Queue sections">
                    <button
                        type="button"
                        role="tab"
                        aria-selected={activeTab === 'pending'}
                        className={`utility-tab${activeTab === 'pending' ? ' is-active' : ''}`}
                        onClick={() => { setActiveTab('pending'); setError(''); }}
                    >
                        <ShoppingCart size={15} />
                        <span>Pending</span>
                        <span className="utility-tab-count">{pendingItems.length}</span>
                    </button>
                    <button
                        type="button"
                        role="tab"
                        aria-selected={activeTab === 'recurring'}
                        className={`utility-tab${activeTab === 'recurring' ? ' is-active' : ''}`}
                        onClick={() => { setActiveTab('recurring'); setError(''); }}
                    >
                        <Repeat size={15} />
                        <span>Recurring</span>
                        <span className="utility-tab-count">{activeRuleCount}</span>
                    </button>
                </div>

                {error && <div className="utility-error" role="alert">{error}</div>}

                <div className="utility-modal-body">
                    {loading ? (
                        <p className="text-muted text-center p-6">Loading...</p>
                    ) : activeTab === 'pending' ? (
                        pendingItems.length === 0 ? (
                            <div className="text-center p-8 text-muted">
                                <p className="font-semibold mb-1">No pending transactions</p>
                                <p className="text-sm">Add delayed payments from the Pending tab inside Add New Transaction.</p>
                            </div>
                        ) : (
                            <div className="utility-list">
                                {pendingItems.map((item) => {
                                    const currency = item.piggy_bank_currency || 'USD';
                                    const bankLabel = item.piggy_bank_name
                                        ? `${item.piggy_bank_name} (${currency})`
                                        : `PiggyBank #${item.piggy_bank_id}`;
                                    const isConfirming = confirmingId === item.id;
                                    return (
                                        <div key={item.id} className="utility-card">
                                            <div className="utility-card-main">
                                                <div className="utility-card-info">
                                                    <div className="flex items-center gap-2 flex-wrap">
                                                        <span className="utility-pill utility-pill-bank">
                                                            <PiggyBankIcon size={12} aria-hidden="true" />
                                                            <span>{bankLabel}</span>
                                                        </span>
                                                        {item.category && <span className="utility-pill utility-pill-soft">{item.category}</span>}
                                                        <span className="text-xs text-muted">
                                                            {item.expected_date
                                                                ? `Expected: ${formatDate(item.expected_date, dateFormat)}`
                                                                : 'Date undecided'}
                                                        </span>
                                                    </div>
                                                    <p className="font-semibold mt-1">
                                                        {item.description || item.category || item.type}
                                                    </p>
                                                </div>
                                                <div className="utility-card-right">
                                                    <span className={`font-bold ${item.amount >= 0 ? 'text-success' : 'text-danger'}`}>
                                                        {formatMoney(item.amount, currency, true)}
                                                    </span>
                                                    <div className="flex items-center gap-2">
                                                        <button
                                                            type="button"
                                                            className="btn btn-primary"
                                                            style={{ padding: '0.38rem 0.75rem', fontSize: '0.82rem' }}
                                                            disabled={busyId === item.id}
                                                            onClick={() => isConfirming ? setConfirmingId(null) : startConfirm(item)}
                                                        >
                                                            <Check size={14} /> {isConfirming ? 'Cancel' : 'Confirm'}
                                                        </button>
                                                        <button
                                                            type="button"
                                                            className="btn btn-secondary"
                                                            style={{ padding: '0.38rem 0.55rem' }}
                                                            disabled={busyId === item.id}
                                                            aria-label={`Delete pending item ${item.description || item.id}`}
                                                            onClick={() => handleDeletePending(item.id)}
                                                        >
                                                            <Trash2 size={14} />
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>

                                            {isConfirming && (
                                                <div className="utility-confirm-row">
                                                    <DateTextField
                                                        id={`confirm-date-${item.id}`}
                                                        label={`Settlement Date (${dateFormat})`}
                                                        value={confirmDateText}
                                                        onChange={setConfirmDateText}
                                                        dateFormat={dateFormat}
                                                    />
                                                    <div>
                                                        <label className="block text-xs font-medium text-text-secondary mb-1">
                                                            Final Amount ({currency})
                                                        </label>
                                                        <input
                                                            type="number"
                                                            step="0.01"
                                                            min="0.01"
                                                            className="input-field"
                                                            value={confirmAmount}
                                                            onChange={(e) => setConfirmAmount(e.target.value)}
                                                        />
                                                    </div>
                                                    <button
                                                        type="button"
                                                        className="btn btn-primary"
                                                        disabled={busyId === item.id}
                                                        onClick={() => handleConfirm(item)}
                                                    >
                                                        {busyId === item.id ? 'Posting...' : 'Post to Ledger'}
                                                    </button>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        )
                    ) : rules.length === 0 ? (
                        <div className="text-center p-8 text-muted">
                            <p className="font-semibold mb-1">No recurring schedules yet</p>
                            <p className="text-sm">Create one from the Recurring tab inside Add New Transaction.</p>
                        </div>
                    ) : (
                        <div className="utility-list">
                            {rules.map((rule) => {
                                const currency = rule.piggy_bank_currency || 'USD';
                                const bankLabel = rule.piggy_bank_name
                                    ? `${rule.piggy_bank_name} (${currency})`
                                    : `PiggyBank #${rule.piggy_bank_id}`;
                                const cadence = rule.interval === 1
                                    ? rule.frequency
                                    : `every ${rule.interval} ${rule.frequency}`;
                                return (
                                    <div key={rule.id} className="utility-card">
                                        <div className="utility-card-main">
                                            <div className="utility-card-info">
                                                <div className="flex items-center gap-2 flex-wrap">
                                                    <span className={`utility-status utility-status-${rule.status}`}>{rule.status}</span>
                                                    <span className="utility-pill utility-pill-bank">
                                                        <PiggyBankIcon size={12} aria-hidden="true" />
                                                        <span>{bankLabel}</span>
                                                    </span>
                                                    <span className="utility-pill utility-pill-soft">{cadence}</span>
                                                </div>
                                                <p className="font-semibold mt-1">
                                                    {rule.description || rule.category || rule.type}
                                                </p>
                                                <p className="text-xs text-muted mt-1">
                                                    Next run: {rule.status === 'stopped' ? 'Stopped' : formatDate(rule.next_run_date, dateFormat)}
                                                    {rule.end_date ? ` · Ends ${formatDate(rule.end_date, dateFormat)}` : ''}
                                                    {` · Posted ${rule.execution_count}×`}
                                                </p>
                                            </div>
                                            <div className="utility-card-right">
                                                <span className={`font-bold ${rule.amount >= 0 ? 'text-success' : 'text-danger'}`}>
                                                    {formatMoney(rule.amount, currency, true)}
                                                </span>
                                                <div className="flex items-center gap-2">
                                                    {rule.status === 'active' && (
                                                        <button
                                                            type="button"
                                                            className="btn btn-secondary"
                                                            style={{ padding: '0.35rem 0.65rem', fontSize: '0.8rem' }}
                                                            disabled={busyId === rule.id}
                                                            onClick={() => handleRuleStatus(rule, 'paused')}
                                                        >
                                                            <Pause size={13} /> Pause
                                                        </button>
                                                    )}
                                                    {rule.status === 'paused' && (
                                                        <button
                                                            type="button"
                                                            className="btn btn-primary"
                                                            style={{ padding: '0.35rem 0.65rem', fontSize: '0.8rem' }}
                                                            disabled={busyId === rule.id}
                                                            onClick={() => handleRuleStatus(rule, 'active')}
                                                        >
                                                            <Play size={13} /> Resume
                                                        </button>
                                                    )}
                                                    {rule.status !== 'stopped' && (
                                                        <button
                                                            type="button"
                                                            className="btn btn-secondary"
                                                            style={{ padding: '0.35rem 0.65rem', fontSize: '0.8rem' }}
                                                            disabled={busyId === rule.id}
                                                            onClick={() => handleRuleStatus(rule, 'stopped')}
                                                        >
                                                            <Square size={13} /> Stop
                                                        </button>
                                                    )}
                                                    <button
                                                        type="button"
                                                        className="btn btn-secondary"
                                                        style={{ padding: '0.35rem 0.55rem' }}
                                                        disabled={busyId === rule.id}
                                                        aria-label={`Delete recurring schedule ${rule.description || rule.id}`}
                                                        onClick={() => handleDeleteRule(rule.id)}
                                                    >
                                                        <Trash2 size={14} />
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            </div>
        </div>,
        document.body,
    );
};
