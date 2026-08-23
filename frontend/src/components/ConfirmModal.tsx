import React, { useEffect, useRef } from 'react';

export type ModalVariant = 'danger' | 'warning' | 'info' | 'success';

interface ConfirmModalProps {
    isOpen: boolean;
    title: string;
    message: string;
    variant?: ModalVariant;
    confirmText?: string;
    cancelText?: string;
    onConfirm: () => void;
    onCancel: () => void;
    /** If true, only show an "OK" button (used for alert-style modals) */
    alertOnly?: boolean;
}

const variantConfig: Record<ModalVariant, { icon: string; color: string; bg: string; hoverBg: string }> = {
    danger: { icon: '🗑️', color: '#ff5e7e', bg: 'rgba(255, 94, 126, 0.12)', hoverBg: 'rgba(255, 94, 126, 0.18)' },
    warning: { icon: '⚠️', color: '#ffb703', bg: 'rgba(255, 183, 3, 0.12)', hoverBg: 'rgba(255, 183, 3, 0.18)' },
    info: { icon: '🐷', color: '#ff8da1', bg: 'rgba(255, 141, 161, 0.12)', hoverBg: 'rgba(255, 141, 161, 0.18)' },
    success: { icon: '✅', color: '#10b981', bg: 'rgba(16, 185, 129, 0.12)', hoverBg: 'rgba(16, 185, 129, 0.18)' },
};

/**
 * A beautiful glassmorphism-style confirmation/alert modal to replace native browser dialogs.
 * Supports danger, warning, info, and success variants with matching icons and color palettes.
 */
export const ConfirmModal: React.FC<ConfirmModalProps> = ({
    isOpen,
    title,
    message,
    variant = 'danger',
    confirmText,
    cancelText = 'Cancel',
    onConfirm,
    onCancel,
    alertOnly = false,
}) => {
    const panelRef = useRef<HTMLDivElement>(null);
    const config = variantConfig[variant];

    // Close on Escape key
    useEffect(() => {
        if (!isOpen) return;
        const handleKey = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onCancel();
        };
        window.addEventListener('keydown', handleKey);
        return () => window.removeEventListener('keydown', handleKey);
    }, [isOpen, onCancel]);

    // Trap focus within the modal
    useEffect(() => {
        if (isOpen && panelRef.current) {
            const firstBtn = panelRef.current.querySelector('button');
            firstBtn?.focus();
        }
    }, [isOpen]);

    if (!isOpen) return null;

    return (
        <div className="confirm-modal-backdrop" onClick={onCancel}>
            <div
                ref={panelRef}
                className="confirm-modal-panel"
                onClick={(e) => e.stopPropagation()}
                role="dialog"
                aria-modal="true"
                aria-labelledby="confirm-modal-title"
            >
                {/* Animated icon badge */}
                <div className="confirm-modal-icon-ring" style={{ background: config.bg }}>
                    <span className="confirm-modal-icon" style={{ fontSize: '2rem' }}>{config.icon}</span>
                </div>

                <h3 id="confirm-modal-title" className="confirm-modal-title">{title}</h3>
                <p className="confirm-modal-message">{message}</p>

                <div className="confirm-modal-actions">
                    {!alertOnly && (
                        <button
                            className="confirm-modal-btn confirm-modal-btn-cancel"
                            onClick={onCancel}
                        >
                            {cancelText}
                        </button>
                    )}
                    <button
                        className="confirm-modal-btn confirm-modal-btn-confirm"
                        style={{
                            background: config.color,
                            boxShadow: `0 4px 20px ${config.color}40`,
                        }}
                        onClick={onConfirm}
                    >
                        {confirmText || (alertOnly ? 'OK' : 'Confirm')}
                    </button>
                </div>
            </div>
        </div>
    );
};
