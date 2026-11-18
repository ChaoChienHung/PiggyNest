import { useEffect, useRef, useState } from 'react';
import { CalendarDays, ChevronLeft, ChevronRight } from 'lucide-react';
import { formatDate, parseDate, todayIsoDate, type DateFormat } from '../utils/dates';

interface DateTextFieldProps {
    id: string;
    label: string;
    value: string;
    onChange: (value: string) => void;
    dateFormat: DateFormat;
    required?: boolean;
    invalid?: boolean;
}

const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const weekdays = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];

export const DateTextField = ({
    id, label, value, onChange, dateFormat, required = false, invalid = false,
}: DateTextFieldProps) => {
    const rootRef = useRef<HTMLDivElement>(null);
    const buttonRef = useRef<HTMLButtonElement>(null);
    const [open, setOpen] = useState(false);
    const [month, setMonth] = useState(() => (parseDate(value, dateFormat) ?? todayIsoDate()).slice(0, 7));
    const selected = parseDate(value, dateFormat);
    const [year, monthNumber] = month.split('-').map(Number);
    const firstWeekday = new Date(year, monthNumber - 1, 1).getDay();
    const daysInMonth = new Date(year, monthNumber, 0).getDate();

    useEffect(() => {
        if (!open) return;
        const closeOutside = (event: PointerEvent) => {
            if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
        };
        const closeEscape = (event: KeyboardEvent) => {
            if (event.key === 'Escape') { setOpen(false); buttonRef.current?.focus(); }
        };
        document.addEventListener('pointerdown', closeOutside);
        document.addEventListener('keydown', closeEscape);
        return () => { document.removeEventListener('pointerdown', closeOutside); document.removeEventListener('keydown', closeEscape); };
    }, [open]);

    const moveMonth = (delta: number) => {
        const next = new Date(year, monthNumber - 1 + delta, 1);
        setMonth(`${next.getFullYear()}-${String(next.getMonth() + 1).padStart(2, '0')}`);
    };
    const choose = (iso: string) => { onChange(formatDate(iso, dateFormat)); setOpen(false); buttonRef.current?.focus(); };

    return <div className="date-text-field" ref={rootRef}>
        <label htmlFor={id}>{label}</label>
        <div className="date-text-control">
            <input id={id} type="text" className="input-field" value={value}
                onChange={event => onChange(event.target.value)} placeholder={dateFormat}
                autoComplete="off" required={required} aria-invalid={invalid} />
            <button ref={buttonRef} type="button" className="date-calendar-button"
                aria-label={`Choose ${label} from calendar`} aria-expanded={open} aria-controls={`${id}-calendar`}
                onClick={() => { if (!open) setMonth((selected ?? todayIsoDate()).slice(0, 7)); setOpen(!open); }}>
                <CalendarDays size={19} aria-hidden="true" />
            </button>
        </div>
        {open && <div id={`${id}-calendar`} className="date-calendar-popover" aria-label={`${label} calendar`}>
            <div className="date-calendar-header">
                <button type="button" aria-label="Previous month" onClick={() => moveMonth(-1)}><ChevronLeft size={18} /></button>
                <strong>{monthNames[monthNumber - 1]} {year}</strong>
                <button type="button" aria-label="Next month" onClick={() => moveMonth(1)}><ChevronRight size={18} /></button>
            </div>
            <div className="date-calendar-grid">
                {weekdays.map(day => <span className="date-calendar-weekday" key={day}>{day}</span>)}
                {Array.from({ length: firstWeekday }, (_, index) => <span key={`empty-${index}`} />)}
                {Array.from({ length: daysInMonth }, (_, index) => {
                    const iso = `${month}-${String(index + 1).padStart(2, '0')}`;
                    return <button type="button" key={iso} aria-label={iso} aria-pressed={selected === iso}
                        className={selected === iso ? 'is-selected' : iso === todayIsoDate() ? 'is-today' : ''}
                        onClick={() => choose(iso)}>{index + 1}</button>;
                })}
            </div>
            <button type="button" className="date-calendar-today" onClick={() => choose(todayIsoDate())}>Today</button>
        </div>}
    </div>;
};
