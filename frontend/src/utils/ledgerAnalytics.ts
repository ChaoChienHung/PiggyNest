import type { CurrencyRate } from '../api/rates';
import type { PiggyBank, Transaction } from '../types';
import { convertAmount } from './currency.ts';
import { isoDatePart } from './dates.ts';

export interface LedgerEntry {
    bank: PiggyBank;
    transaction: Transaction;
}

export interface ConvertedEntry extends LedgerEntry {
    amount: number;
    day: string;
}

export const convertLedger = (
    entries: LedgerEntry[], displayCurrency: string, rates: CurrencyRate[],
) => {
    const missing = new Set<string>();
    const converted: ConvertedEntry[] = [];
    for (const entry of entries) {
        const result = convertAmount(entry.transaction.amount, entry.bank.currency, displayCurrency, rates);
        if (!result) {
            missing.add(entry.bank.currency);
            continue;
        }
        converted.push({ ...entry, amount: result.amount, day: isoDatePart(entry.transaction.date) });
    }
    return { converted, missing: [...missing].sort() };
};

export const periodKey = (day: string, period: 'day' | 'month' | 'year') =>
    period === 'day' ? day : period === 'month' ? day.slice(0, 7) : day.slice(0, 4);

export const isMoneyFlow = (entry: ConvertedEntry) => entry.transaction.type !== 'transfer';

/** The selected banks' balance before a date range, and flow within it. */
export const summarizePeriods = (
    entries: ConvertedEntry[], period: 'day' | 'month' | 'year',
    from: string | null, to: string | null, categories: string[] = [],
) => {
    let openingBalance = 0;
    const rows = new Map<string, {
        period: string; income: number; expense: number; net: number; balance: number;
        transactionCount: number; incomeCount: number; expenseCount: number; netCount: number;
        categoryExpenses: Record<string, number>;
    }>();
    const ordered = [...entries].sort((a, b) => a.day.localeCompare(b.day) || a.transaction.id - b.transaction.id);
    for (const entry of ordered) {
        if (from && entry.day < from) {
            openingBalance += entry.amount;
            continue;
        }
        if (to && entry.day > to) continue;
        if (categories.length && !categories.includes(entry.transaction.category || '')) continue;
        const key = periodKey(entry.day, period);
        const row = rows.get(key) ?? {
            period: key, income: 0, expense: 0, net: 0, balance: 0,
            transactionCount: 0, incomeCount: 0, expenseCount: 0, netCount: 0, categoryExpenses: {},
        };
        row.net += entry.amount;
        row.netCount += 1;
        if (isMoneyFlow(entry)) {
            row.transactionCount += 1;
            if (entry.amount >= 0) {
                row.income += entry.amount;
                row.incomeCount += 1;
            }
            else {
                row.expense -= entry.amount;
                row.expenseCount += 1;
                const category = entry.transaction.category || 'Uncategorized';
                row.categoryExpenses[category] = (row.categoryExpenses[category] || 0) - entry.amount;
            }
        }
        rows.set(key, row);
    }
    let running = openingBalance;
    const periods = [...rows.values()].sort((a, b) => a.period.localeCompare(b.period));
    for (const row of periods) {
        running += row.net;
        row.balance = running;
    }
    return { openingBalance, periods };
};
