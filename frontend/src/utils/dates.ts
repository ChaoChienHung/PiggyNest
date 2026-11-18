/**
 * Transaction dates are calendar dates. The API sends them as ISO strings such as
 * `2026-11-11T00:00:00`; these helpers read and write the date part directly so a
 * time zone offset can never move a transaction to the previous or next day.
 */
export const DATE_FORMATS = ['YYYY-MM-DD', 'DD/MM/YYYY', 'MM/DD/YYYY'] as const;
export type DateFormat = typeof DATE_FORMATS[number];
export const DEFAULT_DATE_FORMAT: DateFormat = 'YYYY-MM-DD';

const pad = (value: number) => String(value).padStart(2, '0');

const isRealDate = (year: number, month: number, day: number) => {
    if (month < 1 || month > 12 || day < 1) return false;
    const check = new Date(Date.UTC(year, month - 1, day));
    return check.getUTCFullYear() === year && check.getUTCMonth() === month - 1 && check.getUTCDate() === day;
};

export const asDateFormat = (value: string | undefined): DateFormat =>
    (DATE_FORMATS as readonly string[]).includes(value ?? '') ? value as DateFormat : DEFAULT_DATE_FORMAT;

/** `2026-11-11T00:00:00` → `2026-11-11` (the calendar date the API stored). */
export const isoDatePart = (apiDate: string) => apiDate.slice(0, 10);

/** Today's local calendar date as `YYYY-MM-DD`. */
export const todayIsoDate = () => {
    const now = new Date();
    return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
};

/** Formats an ISO date or API datetime string in the user's chosen format. */
export const formatDate = (apiDate: string, format: DateFormat) => {
    const [year, month, day] = isoDatePart(apiDate).split('-');
    switch (format) {
        case 'DD/MM/YYYY': return `${day}/${month}/${year}`;
        case 'MM/DD/YYYY': return `${month}/${day}/${year}`;
        default: return `${year}-${month}-${day}`;
    }
};

/**
 * Parses text typed in the user's chosen format and returns `YYYY-MM-DD`, or null
 * when it does not match that format or is not a real date. DD/MM and MM/DD are
 * ambiguous for days 1–12, so the format is never guessed.
 */
export const parseDate = (text: string, format: DateFormat): string | null => {
    const value = text.trim();
    const match = format === 'YYYY-MM-DD'
        ? /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(value)
        : /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(value);
    if (!match) return null;
    let year: number, month: number, day: number;
    if (format === 'YYYY-MM-DD') [year, month, day] = [+match[1], +match[2], +match[3]];
    else if (format === 'DD/MM/YYYY') [day, month, year] = [+match[1], +match[2], +match[3]];
    else [month, day, year] = [+match[1], +match[2], +match[3]];
    if (!isRealDate(year, month, day)) return null;
    return `${year}-${pad(month)}-${pad(day)}`;
};
