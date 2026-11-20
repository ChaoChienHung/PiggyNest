import React, { useCallback, useEffect, useState } from 'react';
import { Bell, ClipboardList, Moon, Sun } from 'lucide-react';
import { pendingApi } from '../api/pending';
import { notificationsApi } from '../api/notifications';
import { useTheme } from '../context/ThemeContext';
import { ScheduledActivityModal } from './ScheduledActivityModal';
import { NotificationCenterModal } from './NotificationCenterModal';

interface HeaderQuickToolsProps {
    refreshSignal?: number;
    onLedgerChanged?: () => void;
    children?: React.ReactNode;
}

/**
 * Shared header action layout (right-edge inward: Settings/Logout -> Dark Mode -> Ledger Queue -> Notifications):
 * [Notifications] [Ledger Queue] [Dark Mode] [Settings / Logout]
 */
export const HeaderQuickTools: React.FC<HeaderQuickToolsProps> = ({
    refreshSignal = 0,
    onLedgerChanged,
    children,
}) => {
    const { theme, toggleTheme } = useTheme();
    const [pendingCount, setPendingCount] = useState(0);
    const [unreadCount, setUnreadCount] = useState(0);
    const [openModal, setOpenModal] = useState<'activity' | 'notifications' | null>(null);

    const refreshCounts = useCallback(async () => {
        try {
            const [pendingList, notifData] = await Promise.all([
                pendingApi.list('pending'),
                notificationsApi.list(),
            ]);
            setPendingCount(pendingList.length);
            setUnreadCount(notifData.unread_count);
        } catch {
            // Silently ignore badge fetch errors when offline or unauthenticated
        }
    }, []);

    useEffect(() => {
        let cancelled = false;
        Promise.all([pendingApi.list('pending'), notificationsApi.list()])
            .then(([pendingList, notifData]) => {
                if (cancelled) return;
                setPendingCount(pendingList.length);
                setUnreadCount(notifData.unread_count);
            })
            .catch(() => {
                // Silently ignore badge fetch errors when offline or unauthenticated
            });
        return () => {
            cancelled = true;
        };
    }, [refreshSignal]);

    const handleChanged = () => {
        refreshCounts();
        onLedgerChanged?.();
    };

    return (
        <>
            <button
                type="button"
                className="btn btn-secondary quick-tool-btn"
                onClick={() => setOpenModal('notifications')}
                aria-label={`Notifications (${unreadCount} unread)`}
                title="Notifications"
            >
                <Bell size={18} />
                {unreadCount > 0 && <span className="quick-tool-badge">{unreadCount}</span>}
            </button>

            <button
                type="button"
                className="btn btn-secondary quick-tool-btn"
                onClick={() => setOpenModal('activity')}
                aria-label={`Ledger Queue (${pendingCount} pending)`}
                title="Ledger Queue"
            >
                <ClipboardList size={18} />
                {pendingCount > 0 && <span className="quick-tool-badge">{pendingCount}</span>}
            </button>

            <button
                type="button"
                className="btn btn-secondary quick-tool-btn"
                onClick={toggleTheme}
                aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
                title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            >
                {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
            </button>

            {children}

            {openModal === 'activity' && (
                <ScheduledActivityModal
                    onClose={() => setOpenModal(null)}
                    onChanged={handleChanged}
                />
            )}
            {openModal === 'notifications' && (
                <NotificationCenterModal
                    onClose={() => setOpenModal(null)}
                    onUnreadChange={setUnreadCount}
                />
            )}
        </>
    );
};
