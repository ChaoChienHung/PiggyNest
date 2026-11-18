import { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { Settings } from '../pages/Settings';

interface SettingsDialogProps {
    onClose: () => void;
    opener?: HTMLElement | null;
}

export const SettingsDialog = ({ onClose, opener }: SettingsDialogProps) => {
    const panelRef = useRef<HTMLDivElement>(null);
    const closeRef = useRef<HTMLButtonElement>(null);

    useEffect(() => {
        const previousOverflow = document.body.style.overflow;
        const scrollX = window.scrollX;
        const scrollY = window.scrollY;
        document.body.style.overflow = 'hidden';
        closeRef.current?.focus();
        return () => {
            document.body.style.overflow = previousOverflow;
            opener?.focus({ preventScroll: true });
            window.scrollTo(scrollX, scrollY);
        };
    }, [opener]);

    useEffect(() => {
        const handleKey = (event: KeyboardEvent) => {
            if (event.key === 'Escape' && !event.defaultPrevented) {
                event.preventDefault();
                onClose();
            }
            if (event.key !== 'Tab') return;
            const focusable = [...(panelRef.current?.querySelectorAll<HTMLElement>(
                'button:not([disabled]), input:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])',
            ) ?? [])].filter(element => element.getClientRects().length > 0);
            if (!focusable.length) return;
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            if (event.shiftKey && (document.activeElement === first || !panelRef.current?.contains(document.activeElement))) {
                event.preventDefault();
                last.focus();
            } else if (!event.shiftKey && (document.activeElement === last || !panelRef.current?.contains(document.activeElement))) {
                event.preventDefault();
                first.focus();
            }
        };
        document.addEventListener('keydown', handleKey);
        return () => document.removeEventListener('keydown', handleKey);
    }, [onClose]);

    return createPortal(
        <div className="settings-dialog-backdrop" onMouseDown={(event) => {
            if (event.target === event.currentTarget) onClose();
        }}>
            <div ref={panelRef} className="settings-dialog-panel" role="dialog" aria-modal="true" aria-labelledby="settings-dialog-title">
                <button ref={closeRef} type="button" className="settings-dialog-close" onClick={onClose} aria-label="Close Settings">✕</button>
                <Settings />
            </div>
        </div>,
        document.body,
    );
};
