import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { ArrowLeft, Bell, CheckCheck, Mail, MailOpen, Trash2, X } from 'lucide-react';
import { notificationsApi } from '../api/notifications';
import { getApiError } from '../api/client';
import type { AppNotification } from '../types';
import { useAuth } from '../context/useAuth';
import { asDateFormat, formatDate } from '../utils/dates';

interface NotificationCenterModalProps {
    onClose: () => void;
    onUnreadChange: (count: number) => void;
}

const kindLabel = (kind: string) => {
    switch (kind) {
        case 'pending_created': return 'Pending Cart';
        case 'pending_confirmed': return 'Confirmed';
        case 'recurring_posted': return 'Recurring';
        case 'budget_alert': return 'Budget Alert';
        default: return 'Notice';
    }
};

export const NotificationCenterModal: React.FC<NotificationCenterModalProps> = ({
    onClose,
    onUnreadChange,
}) => {
    const { user } = useAuth();
    const dateFormat = asDateFormat(user?.date_format);

    const [items, setItems] = useState<AppNotification[]>([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [activeLetter, setActiveLetter] = useState<AppNotification | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const loadAll = async () => {
        try {
            const data = await notificationsApi.list();
            setItems(data.items);
            setUnreadCount(data.unread_count);
            onUnreadChange(data.unread_count);
        } catch (err) {
            setError(getApiError(err, 'Failed to load notifications.'));
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadAll();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        const onKey = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                if (activeLetter) setActiveLetter(null);
                else onClose();
            }
        };
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, [activeLetter, onClose]);

    const openLetter = async (note: AppNotification) => {
        setActiveLetter(note);
        if (!note.is_read) {
            try {
                const updated = await notificationsApi.markRead(note.id);
                setItems((prev) => prev.map((n) => (n.id === note.id ? updated : n)));
                setActiveLetter(updated);
                const nextUnread = Math.max(0, unreadCount - 1);
                setUnreadCount(nextUnread);
                onUnreadChange(nextUnread);
            } catch (err) {
                console.error('Failed to mark notification read', err);
            }
        }
    };

    const handleMarkAllRead = async () => {
        try {
            await notificationsApi.markAllRead();
            setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
            setUnreadCount(0);
            onUnreadChange(0);
        } catch (err) {
            setError(getApiError(err, 'Failed to mark notifications as read.'));
        }
    };

    const handleDelete = async (id: number) => {
        try {
            await notificationsApi.delete(id);
            const removed = items.find((n) => n.id === id);
            setItems((prev) => prev.filter((n) => n.id !== id));
            if (removed && !removed.is_read) {
                const nextUnread = Math.max(0, unreadCount - 1);
                setUnreadCount(nextUnread);
                onUnreadChange(nextUnread);
            }
            if (activeLetter?.id === id) setActiveLetter(null);
        } catch (err) {
            setError(getApiError(err, 'Failed to delete notification.'));
        }
    };

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
                aria-labelledby="notifications-modal-title"
            >
                <div className="utility-modal-header">
                    <div className="flex items-center gap-3">
                        <Bell size={22} className="text-accent-primary" />
                        <div>
                            <h2 id="notifications-modal-title" className="text-xl font-bold" style={{ marginBottom: 0 }}>
                                Notifications
                            </h2>
                            <p className="text-xs text-muted">
                                Click any message to open it as a letter.
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        {unreadCount > 0 && !activeLetter && (
                            <button
                                type="button"
                                className="btn btn-secondary"
                                style={{ padding: '0.4rem 0.8rem', fontSize: '0.84rem' }}
                                onClick={handleMarkAllRead}
                            >
                                <CheckCheck size={15} /> Mark all read
                            </button>
                        )}
                        <button type="button" className="btn btn-secondary utility-icon-close" onClick={onClose} aria-label="Close Notifications">
                            <X size={18} />
                        </button>
                    </div>
                </div>

                {error && <div className="utility-error" role="alert">{error}</div>}

                <div className="utility-modal-body">
                    {activeLetter ? (
                        <article className="notification-letter animate-fade-in">
                            <div className="notification-letter-toolbar">
                                <button
                                    type="button"
                                    className="btn btn-secondary"
                                    style={{ padding: '0.35rem 0.75rem', fontSize: '0.84rem' }}
                                    onClick={() => setActiveLetter(null)}
                                >
                                    <ArrowLeft size={14} /> Back to Inbox
                                </button>
                                <button
                                    type="button"
                                    className="btn btn-secondary"
                                    style={{ padding: '0.35rem 0.75rem', fontSize: '0.84rem' }}
                                    onClick={() => handleDelete(activeLetter.id)}
                                >
                                    <Trash2 size={14} /> Delete
                                </button>
                            </div>
                            <div className="notification-letter-paper">
                                <div className="flex items-center justify-between gap-2 flex-wrap mb-3">
                                    <span className="utility-pill">{kindLabel(activeLetter.kind)}</span>
                                    {activeLetter.created_at && (
                                        <span className="text-xs text-muted">
                                            {formatDate(activeLetter.created_at, dateFormat)}
                                        </span>
                                    )}
                                </div>
                                <h3 className="text-lg font-bold mb-4">{activeLetter.title}</h3>
                                <div className="notification-letter-body">{activeLetter.body}</div>
                                <div className="notification-letter-footer">
                                    PiggyNest Notification Center
                                </div>
                            </div>
                        </article>
                    ) : loading ? (
                        <p className="text-muted text-center p-6">Loading notifications...</p>
                    ) : items.length === 0 ? (
                        <div className="text-center p-8 text-muted">
                            <p className="font-semibold mb-1">No notifications yet</p>
                            <p className="text-sm">Pending cart confirmations and recurring postings will arrive here as letters.</p>
                        </div>
                    ) : (
                        <div className="utility-list">
                            {items.map((note) => (
                                <div
                                    key={note.id}
                                    className={`utility-card notification-row${note.is_read ? '' : ' is-unread'}`}
                                >
                                    <button
                                        type="button"
                                        className="notification-row-btn"
                                        onClick={() => openLetter(note)}
                                    >
                                        <span className="notification-row-icon" aria-hidden="true">
                                            {note.is_read ? <MailOpen size={18} /> : <Mail size={18} />}
                                        </span>
                                        <span className="notification-row-content">
                                            <span className="flex items-center gap-2 flex-wrap">
                                                <span className="utility-pill utility-pill-soft">{kindLabel(note.kind)}</span>
                                                {!note.is_read && <span className="notification-unread-dot" aria-label="Unread" />}
                                                {note.created_at && (
                                                    <span className="text-xs text-muted">
                                                        {formatDate(note.created_at, dateFormat)}
                                                    </span>
                                                )}
                                            </span>
                                            <span className="font-semibold block mt-1">{note.title}</span>
                                            <span className="text-xs text-muted block notification-preview">
                                                {note.body.split('\n')[0]}
                                            </span>
                                        </span>
                                    </button>
                                    <button
                                        type="button"
                                        className="btn btn-secondary"
                                        style={{ padding: '0.35rem 0.55rem', flexShrink: 0 }}
                                        aria-label={`Delete notification ${note.title}`}
                                        onClick={() => handleDelete(note.id)}
                                    >
                                        <Trash2 size={14} />
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>,
        document.body,
    );
};
