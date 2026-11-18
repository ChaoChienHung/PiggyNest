import type { summarizePeriods } from './ledgerAnalytics';

type PeriodRow = ReturnType<typeof summarizePeriods>['periods'][number];
type Interval = 'day' | 'month' | 'year';
type Metric = 'income' | 'expense' | 'net';

const nextPeriod = (key: string, interval: Interval) => {
    if (interval === 'year') return String(Number(key) + 1);
    if (interval === 'month') {
        const [year, month] = key.split('-').map(Number);
        return month === 12 ? `${year + 1}-01` : `${year}-${String(month + 1).padStart(2, '0')}`;
    }
    const [year, month, day] = key.split('-').map(Number);
    const next = new Date(Date.UTC(year, month - 1, day + 1));
    return next.toISOString().slice(0, 10);
};

/** Includes empty calendar periods so averages use calendar time, not activity only. */
export const fillReportPeriods = (
    rows: PeriodRow[], interval: Interval, from: string | null, to: string | null,
): PeriodRow[] => {
    const first = from?.slice(0, interval === 'day' ? 10 : interval === 'month' ? 7 : 4) ?? rows[0]?.period;
    const last = to?.slice(0, interval === 'day' ? 10 : interval === 'month' ? 7 : 4) ?? rows[rows.length - 1]?.period;
    if (!first || !last || first > last) return [];
    const byPeriod = new Map(rows.map(row => [row.period, row]));
    const filled: PeriodRow[] = [];
    let balance = 0;
    for (let key = first; key <= last; key = nextPeriod(key, interval)) {
        const existing = byPeriod.get(key);
        if (existing) {
            balance = existing.balance;
            filled.push(existing);
        } else filled.push({
            period: key, income: 0, expense: 0, net: 0, balance,
            transactionCount: 0, incomeCount: 0, expenseCount: 0, netCount: 0,
            categoryExpenses: {},
        });
    }
    return filled;
};

export const metricSummary = (rows: PeriodRow[], metric: Metric) => {
    if (!rows.length) return null;
    const total = rows.reduce((sum, row) => sum + row[metric], 0);
    const countKey = metric === 'income' ? 'incomeCount' : metric === 'expense' ? 'expenseCount' : 'netCount';
    const count = rows.reduce((sum, row) => sum + row[countKey], 0);
    const min = rows.reduce((best, row) => row[metric] < best[metric] ? row : best);
    const max = rows.reduce((best, row) => row[metric] > best[metric] ? row : best);
    return { total, average: total / rows.length, min: min[metric], minPeriod: min.period,
        max: max[metric], maxPeriod: max.period, count, periods: rows.length };
};
