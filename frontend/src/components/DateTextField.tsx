import { useRef } from 'react';
import { CalendarDays } from 'lucide-react';
import { formatDate, parseDate, type DateFormat } from '../utils/dates';

interface DateTextFieldProps {
    id: string;
    label: string;
    value: string;
    onChange: (value: string) => void;
    dateFormat: DateFormat;
    required?: boolean;
    invalid?: boolean;
}

/** Keeps typed dates in the user's format while the native picker uses ISO dates. */
export const DateTextField = ({
    id, label, value, onChange, dateFormat, required = false, invalid = false,
}: DateTextFieldProps) => {
    const pickerRef = useRef<HTMLInputElement>(null);
    const openCalendar = () => {
        const picker = pickerRef.current;
        if (!picker) return;
        try {
            if (picker.showPicker) picker.showPicker();
            else picker.click();
        } catch {
            picker.focus();
            picker.click();
        }
    };

    return <div className="date-text-field">
        <label htmlFor={id}>{label}</label>
        <div className="date-text-control">
            <input id={id} type="text" className="input-field" value={value}
                onChange={event => onChange(event.target.value)} placeholder={dateFormat}
                autoComplete="off" required={required} aria-invalid={invalid} />
            <button type="button" className="date-calendar-button" aria-label={`Choose ${label} from calendar`} onClick={openCalendar}>
                <CalendarDays size={19} aria-hidden="true" />
            </button>
            <input ref={pickerRef} className="date-native-picker" type="date" tabIndex={-1}
                aria-label={`${label} calendar picker`} value={parseDate(value, dateFormat) ?? ''}
                onChange={event => { if (event.target.value) onChange(formatDate(event.target.value, dateFormat)); }} />
        </div>
    </div>;
};
