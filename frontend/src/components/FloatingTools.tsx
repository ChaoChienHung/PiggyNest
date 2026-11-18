import { useRef, useState } from 'react';

interface FloatingToolsProps {
    showAnalytics: boolean;
    setShowAnalytics: (show: boolean) => void;
}

export const FloatingTools = ({ showAnalytics, setShowAnalytics }: FloatingToolsProps) => {
    const [open, setOpen] = useState(false);
    const triggerRef = useRef<HTMLButtonElement>(null);

    return (
        <div
            className={`floating-tools${open ? ' is-open' : ''}`}
            onKeyDown={(event) => {
                if (event.key === 'Escape') {
                    setOpen(false);
                    triggerRef.current?.focus();
                }
            }}
            onBlur={(event) => {
                if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
            }}
        >
            <div className="floating-tools-actions" id="floating-tools-actions">
                <button
                    type="button"
                    className="floating-tools-action"
                    onClick={() => {
                        setShowAnalytics(!showAnalytics);
                        setOpen(false);
                    }}
                >
                    {showAnalytics ? 'Hide Graph Analysis' : 'Graph Analysis'}
                </button>
            </div>
            <button
                ref={triggerRef}
                type="button"
                className="floating-tools-trigger"
                aria-label="Additional tools"
                aria-expanded={open}
                aria-controls="floating-tools-actions"
                onClick={() => setOpen(!open)}
            >
                🐷
            </button>
        </div>
    );
};
