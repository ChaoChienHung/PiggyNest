import { useEffect, useId, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { ChevronDown } from 'lucide-react';

export interface SelectOption {
    value: string;
    label: string;
    disabled?: boolean;
}

interface ThemedSelectProps {
    value: string;
    options: SelectOption[];
    onChange: (value: string) => void;
    id?: string;
    ariaLabel?: string;
    disabled?: boolean;
    className?: string;
}

export const ThemedSelect = ({
    value, options, onChange, id, ariaLabel, disabled = false, className = '',
}: ThemedSelectProps) => {
    const listboxId = useId();
    const buttonRef = useRef<HTMLButtonElement>(null);
    const menuRef = useRef<HTMLDivElement>(null);
    const typeaheadRef = useRef({ text: '', at: 0 });
    const [open, setOpen] = useState(false);
    const [active, setActive] = useState(0);
    const [placement, setPlacement] = useState<React.CSSProperties>({});

    const selected = options.findIndex(option => option.value === value);
    const enabled = (index: number) => options[index] && !options[index].disabled;

    const positionMenu = () => {
        const rect = buttonRef.current?.getBoundingClientRect();
        if (!rect) return;
        const width = Math.min(Math.max(rect.width, 220), window.innerWidth - 16);
        const below = window.innerHeight - rect.bottom - 8;
        const above = rect.top - 8;
        const upwards = below < 200 && above > below;
        const maxHeight = Math.max(80, Math.min(300, upwards ? above - 8 : below - 8));
        setPlacement({
            left: Math.max(8, Math.min(rect.left, window.innerWidth - width - 8)),
            top: upwards ? Math.max(8, rect.top - maxHeight - 6) : rect.bottom + 6,
            width,
            maxHeight,
        });
    };

    const openMenu = (index = selected) => {
        if (disabled) return;
        positionMenu();
        setActive(enabled(index) ? index : options.findIndex((_, i) => enabled(i)));
        setOpen(true);
    };

    const move = (direction: number) => {
        if (!options.length) return;
        let next = open ? active : selected;
        for (let step = 0; step < options.length; step++) {
            next = (next + direction + options.length) % options.length;
            if (enabled(next)) {
                if (!open) openMenu(next);
                else setActive(next);
                return;
            }
        }
    };

    const choose = (index: number) => {
        if (!enabled(index)) return;
        onChange(options[index].value);
        setOpen(false);
        buttonRef.current?.focus();
    };

    useEffect(() => {
        if (!open) return;
        const update = () => positionMenu();
        const outside = (event: PointerEvent) => {
            const target = event.target as Node;
            if (!buttonRef.current?.contains(target) && !menuRef.current?.contains(target)) setOpen(false);
        };
        window.addEventListener('resize', update);
        window.addEventListener('scroll', update, true);
        document.addEventListener('pointerdown', outside);
        return () => {
            window.removeEventListener('resize', update);
            window.removeEventListener('scroll', update, true);
            document.removeEventListener('pointerdown', outside);
        };
    }, [open]);

    useEffect(() => {
        if (open && active >= 0) {
            document.getElementById(`${listboxId}-option-${active}`)?.scrollIntoView({ block: 'nearest' });
        }
    }, [open, active, listboxId]);

    const handleKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>) => {
        if (disabled) return;
        if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
            event.preventDefault();
            move(event.key === 'ArrowDown' ? 1 : -1);
        } else if (event.key === 'Home' || event.key === 'End') {
            event.preventDefault();
            const indices = options.map((_, i) => i).filter(enabled);
            const next = event.key === 'Home' ? indices[0] : indices[indices.length - 1];
            if (next !== undefined) {
                if (open) setActive(next);
                else openMenu(next);
            }
        } else if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            if (open) choose(active);
            else openMenu();
        } else if (event.key === 'Escape' && open) {
            event.preventDefault();
            setOpen(false);
        } else if (event.key === 'Tab') {
            setOpen(false);
        } else if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
            const now = Date.now();
            const previous = typeaheadRef.current;
            const text = (now - previous.at < 700 ? previous.text : '') + event.key.toLowerCase();
            typeaheadRef.current = { text, at: now };
            const match = options.findIndex(option => !option.disabled && option.label.toLowerCase().startsWith(text));
            if (match >= 0) {
                if (open) setActive(match);
                else openMenu(match);
            }
        }
    };

    return (
        <>
            <button
                ref={buttonRef}
                id={id}
                type="button"
                role="combobox"
                aria-label={ariaLabel}
                aria-haspopup="listbox"
                aria-expanded={open}
                aria-controls={listboxId}
                aria-activedescendant={open && active >= 0 ? `${listboxId}-option-${active}` : undefined}
                disabled={disabled}
                className={`themed-select ${className}`.trim()}
                onClick={() => open ? setOpen(false) : openMenu()}
                onKeyDown={handleKeyDown}
                onBlur={(event) => {
                    if (!menuRef.current?.contains(event.relatedTarget)) setOpen(false);
                }}
            >
                <span className="themed-select-label">{selected >= 0 ? options[selected].label : 'Select...'}</span>
                <ChevronDown size={18} aria-hidden="true" />
            </button>
            {open && createPortal(
                <div ref={menuRef} id={listboxId} role="listbox" className="themed-select-menu" style={placement}>
                    {options.map((option, index) => (
                        <div
                            key={`${option.value}-${index}`}
                            id={`${listboxId}-option-${index}`}
                            role="option"
                            aria-selected={option.value === value}
                            aria-disabled={option.disabled || undefined}
                            className={`themed-select-option${index === active ? ' is-active' : ''}${option.disabled ? ' is-disabled' : ''}`}
                            onMouseEnter={() => { if (!option.disabled) setActive(index); }}
                            onMouseDown={event => event.preventDefault()}
                            onClick={() => choose(index)}
                        >
                            {option.label}
                        </div>
                    ))}
                </div>,
                document.body,
            )}
        </>
    );
};
