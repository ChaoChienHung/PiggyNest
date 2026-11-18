import { useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
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

type CalendarView = 'days' | 'months' | 'years';
const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const weekdays = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];
const padMonth = (value: number) => String(value).padStart(2, '0');

export const DateTextField = ({
    id, label, value, onChange, dateFormat, required = false, invalid = false,
}: DateTextFieldProps) => {
    const rootRef = useRef<HTMLDivElement>(null);
    const buttonRef = useRef<HTMLButtonElement>(null);
    const popoverRef = useRef<HTMLDivElement>(null);
    const [open, setOpen] = useState(false);
    const [view, setView] = useState<CalendarView>('days');
    const [month, setMonth] = useState(() => (parseDate(value, dateFormat) ?? todayIsoDate()).slice(0, 7));
    const [yearPage, setYearPage] = useState(2020);
    const [position, setPosition] = useState({ top: 0, left: 0 });
    const selected = parseDate(value, dateFormat);
    const [year, monthNumber] = month.split('-').map(Number);
    const firstWeekday = new Date(year, monthNumber - 1, 1).getDay();
    const daysInMonth = new Date(year, monthNumber, 0).getDate();

    useLayoutEffect(() => {
        if (!open) return;
        const updatePosition = () => {
            const anchor = buttonRef.current?.getBoundingClientRect();
            if (!anchor) return;
            const width = popoverRef.current?.offsetWidth ?? 304;
            const height = popoverRef.current?.offsetHeight ?? 360;
            const below = window.innerHeight - anchor.bottom >= height + 12;
            setPosition({
                top: below ? anchor.bottom + 10 : Math.max(8, anchor.top - height - 10),
                left: Math.max(8, Math.min(anchor.right - width, window.innerWidth - width - 8)),
            });
        };
        const closeOutside = (event: PointerEvent) => {
            const target = event.target as Node;
            if (!rootRef.current?.contains(target) && !popoverRef.current?.contains(target)) setOpen(false);
        };
        const closeEscape = (event: KeyboardEvent) => {
            if (event.key === 'Escape') { setOpen(false); buttonRef.current?.focus(); }
        };
        updatePosition();
        document.addEventListener('pointerdown', closeOutside);
        document.addEventListener('keydown', closeEscape);
        window.addEventListener('resize', updatePosition);
        window.addEventListener('scroll', updatePosition, true);
        return () => {
            document.removeEventListener('pointerdown', closeOutside);
            document.removeEventListener('keydown', closeEscape);
            window.removeEventListener('resize', updatePosition);
            window.removeEventListener('scroll', updatePosition, true);
        };
    }, [open, view, month, yearPage]);

    const move = (delta: number) => {
        if (view === 'years') { setYearPage(yearPage + delta * 10); return; }
        if (view === 'months') { setMonth(`${year + delta}-${padMonth(monthNumber)}`); return; }
        const next = new Date(year, monthNumber - 1 + delta, 1);
        setMonth(`${next.getFullYear()}-${padMonth(next.getMonth() + 1)}`);
    };
    const choose = (iso: string) => { onChange(formatDate(iso, dateFormat)); setOpen(false); buttonRef.current?.focus(); };
    const openCalendar = () => {
        if (!open) {
            const initial = (selected ?? todayIsoDate()).slice(0, 7);
            setMonth(initial);
            setYearPage(Math.floor(Number(initial.slice(0, 4)) / 10) * 10);
            setView('days');
        }
        setOpen(!open);
    };

    return <div className="date-text-field" ref={rootRef}>
        <label htmlFor={id}>{label}</label>
        <div className="date-text-control">
            <input id={id} type="text" className="input-field" value={value}
                onChange={event => onChange(event.target.value)} placeholder={dateFormat}
                autoComplete="off" required={required} aria-invalid={invalid} />
            <button ref={buttonRef} type="button" className="date-calendar-button"
                aria-label={`Choose ${label} from calendar`} aria-expanded={open} aria-controls={`${id}-calendar`}
                onClick={openCalendar}>
                <CalendarDays size={19} aria-hidden="true" />
            </button>
        </div>
        {open && createPortal(<div ref={popoverRef} id={`${id}-calendar`} className="date-calendar-popover"
            aria-label={`${label} calendar`} style={{ top: position.top, left: position.left }}>
            <div className="date-calendar-header">
                <button type="button" aria-label={view === 'days' ? 'Previous month' : view === 'months' ? 'Previous year' : 'Previous decade'} onClick={() => move(-1)}><ChevronLeft size={18} /></button>
                <div className="date-calendar-title">
                    {view === 'years' ? <strong>{yearPage}–{yearPage + 9}</strong> : <>
                        <button type="button" className={view === 'months' ? 'is-current' : ''}
                            aria-label="Choose month" onClick={() => setView('months')}>{monthNames[monthNumber - 1]}</button>
                        <button type="button" aria-label="Choose year" onClick={() => { setYearPage(Math.floor(year / 10) * 10); setView('years'); }}>{year}</button>
                    </>}
                </div>
                <button type="button" aria-label={view === 'days' ? 'Next month' : view === 'months' ? 'Next year' : 'Next decade'} onClick={() => move(1)}><ChevronRight size={18} /></button>
            </div>
            {view === 'days' ? <div className="date-calendar-grid">
                {weekdays.map(day => <span className="date-calendar-weekday" key={day}>{day}</span>)}
                {Array.from({ length: firstWeekday }, (_, index) => <span key={`empty-${index}`} />)}
                {Array.from({ length: daysInMonth }, (_, index) => {
                    const iso = `${month}-${padMonth(index + 1)}`;
                    return <button type="button" key={iso} aria-label={iso} aria-pressed={selected === iso}
                        className={selected === iso ? 'is-selected' : iso === todayIsoDate() ? 'is-today' : ''}
                        onClick={() => choose(iso)}>{index + 1}</button>;
                })}
            </div> : <div className="date-calendar-choices">
                {view === 'months' ? monthNames.map((name, index) => <button type="button" key={name}
                    aria-label={`Choose ${name}`} className={monthNumber === index + 1 ? 'is-selected' : ''}
                    onClick={() => { setMonth(`${year}-${padMonth(index + 1)}`); setView('days'); }}>{name.slice(0, 3)}</button>)
                    : Array.from({ length: 10 }, (_, index) => yearPage + index).map(option => <button type="button" key={option}
                        aria-label={`Choose year ${option}`} className={option === year ? 'is-selected' : ''}
                        onClick={() => { setMonth(`${option}-${padMonth(monthNumber)}`); setView('months'); }}>{option}</button>)}
            </div>}
            <button type="button" className="date-calendar-today" onClick={() => choose(todayIsoDate())}>Today</button>
        </div>, document.body)}
    </div>;
};
