import { useEffect, useRef, useState } from 'react';
import { BarChart3, FileText, PiggyBank } from 'lucide-react';
import { Link } from 'react-router-dom';
import { createPortal } from 'react-dom';

interface FloatingToolsProps { bankId?: number }

export const FloatingTools = ({ bankId }: FloatingToolsProps) => {
    const [open, setOpen] = useState(false);
    const rootRef = useRef<HTMLDivElement>(null);
    const triggerRef = useRef<HTMLButtonElement>(null);
    useEffect(() => {
        if (!open) return;
        const closeOutside = (event: PointerEvent) => {
            if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
        };
        document.addEventListener('pointerdown', closeOutside);
        return () => document.removeEventListener('pointerdown', closeOutside);
    }, [open]);
    const suffix = bankId ? `?bank=${bankId}` : '';
    return createPortal(<div ref={rootRef} className={`floating-tools${open ? ' is-open' : ''}`}
        onPointerEnter={event => { if (event.pointerType === 'mouse') setOpen(true); }}
        onPointerLeave={event => { if (event.pointerType === 'mouse') setOpen(false); }}
        onBlur={event => { if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false); }}
        onKeyDown={event => { if (event.key === 'Escape') { setOpen(false); triggerRef.current?.focus(); } }}>
        <div className="floating-tools-actions" id="floating-tools-actions">
            <Link to={`/analysis${suffix}`} state={{ from: bankId ? `/piggybanks/${bankId}` : '/' }}
                className="floating-tools-action" aria-label="Graph Analysis" title="Graph Analysis" onClick={() => setOpen(false)}>
                <BarChart3 size={23} aria-hidden="true" />
            </Link>
            <Link to={`/reports${suffix}`} state={{ from: bankId ? `/piggybanks/${bankId}` : '/' }}
                className="floating-tools-action" aria-label="Reports" title="Reports" onClick={() => setOpen(false)}>
                <FileText size={23} aria-hidden="true" />
            </Link>
        </div>
        <button ref={triggerRef} type="button" className="floating-tools-trigger"
            aria-label="Additional tools" aria-expanded={open} aria-controls="floating-tools-actions"
            onClick={() => setOpen(!open)}><PiggyBank size={41} strokeWidth={1.9} aria-hidden="true" /></button>
    </div>, document.body);
};
