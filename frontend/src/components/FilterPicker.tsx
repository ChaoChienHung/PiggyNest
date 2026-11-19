import { useEffect, useRef, useState } from 'react';

interface FilterOption<T extends string | number> {
    value: T;
    label: string;
}

interface FilterPickerProps<T extends string | number> {
    label: string;
    options: FilterOption<T>[];
    selected: T[];
    onChange: (values: T[]) => void;
    emptyLabel: string;
    clearLabel: string;
    allLabel?: string;
}

export const FilterPicker = <T extends string | number>({
    label, options, selected, onChange, emptyLabel, clearLabel, allLabel = 'Select all',
}: FilterPickerProps<T>) => {
    const detailsRef = useRef<HTMLDetailsElement>(null);
    const summaryRef = useRef<HTMLElement>(null);
    const [query, setQuery] = useState('');
    const visible = options.filter(option => option.label.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()));
    const allSelected = options.length > 0 && options.every(option => selected.includes(option.value));
    const summary = allSelected
        ? `All (${options.length})`
        : selected.length === 0 ? emptyLabel : `${selected.length} of ${options.length}`;

    useEffect(() => {
        const closeOutside = (event: PointerEvent) => {
            if (detailsRef.current && !detailsRef.current.contains(event.target as Node)) detailsRef.current.open = false;
        };
        const closeEscape = (event: KeyboardEvent) => {
            if (event.key === 'Escape' && detailsRef.current?.open) {
                detailsRef.current.open = false;
                summaryRef.current?.focus();
            }
        };
        document.addEventListener('pointerdown', closeOutside);
        document.addEventListener('keydown', closeEscape);
        return () => {
            document.removeEventListener('pointerdown', closeOutside);
            document.removeEventListener('keydown', closeEscape);
        };
    }, []);

    return <div className="filter-picker">
        <span className="filter-picker-label">{label}</span>
        <details ref={detailsRef} onToggle={event => {
            if (!event.currentTarget.open) setQuery('');
        }}>
            <summary ref={summaryRef} aria-label={`${label}: ${summary}`}>
                <span className="filter-picker-count">{summary}</span>
            </summary>
            <div className="filter-picker-menu">
                <div className="filter-picker-actions">
                    <button type="button" onClick={() => {
                        onChange(options.map(option => option.value));
                        if (detailsRef.current) detailsRef.current.open = false;
                    }}>{allLabel}</button>
                    <button type="button" onClick={() => {
                        onChange([]);
                        if (detailsRef.current) detailsRef.current.open = false;
                    }}>{clearLabel}</button>
                </div>
                <input type="search" className="input-field filter-picker-search" value={query}
                    onChange={event => setQuery(event.target.value)} placeholder={`Search ${label.toLowerCase()}`}
                    aria-label={`Search ${label}`} />
                <div className="filter-picker-list">
                    {visible.map(option => <label key={option.value} className="filter-picker-option">
                        <input type="checkbox" checked={selected.includes(option.value)} onChange={event => onChange(event.target.checked
                            ? [...selected, option.value] : selected.filter(value => value !== option.value))} />
                        <span>{option.label}</span>
                    </label>)}
                    {visible.length === 0 && <p className="text-sm text-muted">No matches.</p>}
                </div>
            </div>
        </details>
    </div>;
};
