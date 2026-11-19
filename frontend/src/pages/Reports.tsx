import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import { useRates } from '../context/useRates';
import { useLedgerEntries } from '../context/useLedgerEntries';
import { authApi } from '../api/auth';
import { asDateFormat, formatPeriod, parseDate } from '../utils/dates';
import { convertLedger, summarizePeriods } from '../utils/ledgerAnalytics';
import { fillReportPeriods, metricSummary } from '../utils/reportMath';
import { formatMoney } from '../utils/money';
import { ThemedSelect } from '../components/ThemedSelect';
import { FilterPicker } from '../components/FilterPicker';
import { DateTextField } from '../components/DateTextField';
import { FloatingTools } from '../components/FloatingTools';
import { displayCurrencyOptions, rateSummary } from '../utils/currency';

const intervals = [
    { key: 'day', label: 'Daily' }, { key: 'month', label: 'Monthly' }, { key: 'year', label: 'Yearly' },
] as const;
const metrics = [
    { key: 'income', label: 'Income' }, { key: 'expense', label: 'Spending' }, { key: 'net', label: 'Net change' },
] as const;

export const Reports = () => {
    const [params] = useSearchParams();
    const initialBank = Number(params.get('bank'));
    const { user, updateUser } = useAuth();
    const { rates, isLoading: ratesLoading } = useRates();
    const { banks, entries, loading, error } = useLedgerEntries();
    const [selectedIds, setSelectedIds] = useState<number[] | null>(Number.isSafeInteger(initialBank) && initialBank > 0 ? [initialBank] : null);
    const [categories, setCategories] = useState<string[]>([]);
    const [fromText, setFromText] = useState('');
    const [toText, setToText] = useState('');
    const [from, setFrom] = useState<string | null>(null);
    const [to, setTo] = useState<string | null>(null);
    const dateFormat = asDateFormat(user?.date_format);
    const displayCurrency = user?.display_currency ?? 'NTD';
    const hidden = user?.net_worth_hidden ?? false;
    const selected = selectedIds ?? banks.map(bank => bank.id);
    const bankEntries = entries.filter(entry => selected.includes(entry.bank.id));
    const categoryOptions = [...new Set(bankEntries.map(entry => entry.transaction.category || ''))].sort();
    const { converted, missing } = convertLedger(bankEntries, displayCurrency, rates);
    const parsedFrom = fromText.trim() ? parseDate(fromText, dateFormat) : null;
    const parsedTo = toText.trim() ? parseDate(toText, dateFormat) : null;
    const rangeError = fromText.trim() && !parsedFrom ? `Start date must use ${dateFormat}.`
        : toText.trim() && !parsedTo ? `End date must use ${dateFormat}.`
        : parsedFrom && parsedTo && parsedFrom > parsedTo ? 'Start date must be on or before end date.' : '';
    const applyRange = (nextFrom: string, nextTo: string) => {
        setFromText(nextFrom);
        setToText(nextTo);
        const start = nextFrom.trim() ? parseDate(nextFrom, dateFormat) : null;
        const end = nextTo.trim() ? parseDate(nextTo, dateFormat) : null;
        if ((!nextFrom.trim() || start) && (!nextTo.trim() || end) && (!start || !end || start <= end)) {
            setFrom(start);
            setTo(end);
        }
    };
    const amount = (value: number) => hidden ? '****' : formatMoney(value, displayCurrency);
    const ratesTitle = hidden ? undefined : rateSummary(banks.filter(bank => selected.includes(bank.id)).map(bank => bank.currency), displayCurrency, rates);
    const periodLabel = (key: string, interval: 'day' | 'month' | 'year') => formatPeriod(key, interval, dateFormat);

    return <main className="container page-layout-container with-floating-tools animate-fade-in reports-page">
        <header className="reports-header">
            <div><Link to={initialBank ? `/piggybanks/${initialBank}` : '/'} className="text-accent-primary">← Back</Link>
                <h1 className="dashboard-title">Reports</h1>
                <p className="text-text-secondary">Numeric summaries for your selected PiggyBanks and dates.</p></div>
            <ThemedSelect ariaLabel="Report currency" className="analytics-select" value={displayCurrency}
                onChange={async value => { try { updateUser(await authApi.updateDisplayCurrency(value)); } catch (err) { console.error(err); } }}
                options={displayCurrencyOptions(banks.map(bank => bank.currency), displayCurrency)} />
        </header>
        <section className="glass-panel p-6 mb-8 reports-filter-panel" aria-label="Report filters">
            <div className="reports-filter-grid">
                <FilterPicker label="PiggyBanks" options={banks.map(bank => ({ value: bank.id, label: `${bank.name} (${bank.currency})` }))}
                    selected={selected} onChange={values => { setSelectedIds(values); setCategories([]); }} emptyLabel="None" clearLabel="Clear all" />
                <FilterPicker label="Categories" options={categoryOptions.map(category => ({ value: category, label: category || 'Uncategorized' }))}
                    selected={categories} onChange={setCategories} emptyLabel="All" clearLabel="All categories" emptyMeansAll />
            <div className="analytics-date-filter">
                <DateTextField id="reports-date-from" label="From" value={fromText}
                    onChange={value => applyRange(value, toText)} dateFormat={dateFormat} invalid={!!rangeError} />
                <DateTextField id="reports-date-to" label="To" value={toText}
                    onChange={value => applyRange(fromText, value)} dateFormat={dateFormat} invalid={!!rangeError} />
                {rangeError && <span className="text-sm text-danger" role="alert">{rangeError}</span>}
            </div>
            </div>
        </section>
        <p className="text-sm text-text-secondary mb-6">Averages include periods with no transactions. Without a date filter, periods run from the first to the last matching transaction. PiggyBank transfers are excluded from income and spending.</p>
        {(loading || ratesLoading) ? <p className="text-muted">Loading reports…</p>
            : error ? <p className="text-danger" role="alert">{error}</p>
            : selected.length === 0 ? <p className="text-muted">Select a PiggyBank to see reports.</p>
            : missing.length > 0 ? <p className="text-danger">Rate needed for {missing.join(', ')}. <Link to="/settings">Open Settings</Link></p>
            : intervals.map(interval => {
                const rows = summarizePeriods(converted, interval.key, from, to, categories).periods;
                const filled = fillReportPeriods(rows, interval.key, from, to);
                return <section key={interval.key} className="reports-section">
                    <h2 className="text-xl font-bold mb-3">{interval.label}</h2>
                    {filled.length === 0 ? <p className="text-muted">No periods in this range.</p> : <div className="reports-grid">
                        {metrics.map(metric => {
                            const summary = metricSummary(filled, metric.key)!;
                            return <article key={metric.key} className="glass-panel reports-card">
                                <h3 className="font-semibold">{metric.label}</h3>
                                <dl>
                                    <div><dt>Total</dt><dd title={ratesTitle}>{amount(summary.total)}</dd></div>
                                    <div><dt>Average</dt><dd title={ratesTitle}>{amount(summary.average)} per {interval.key}</dd></div>
                                    <div><dt>Minimum</dt><dd title={ratesTitle}>{amount(summary.min)} <small>({periodLabel(summary.minPeriod, interval.key)})</small></dd></div>
                                    <div><dt>Maximum</dt><dd title={ratesTitle}>{amount(summary.max)} <small>({periodLabel(summary.maxPeriod, interval.key)})</small></dd></div>
                                    <div><dt>Transactions</dt><dd>{summary.count}</dd></div>
                                </dl>
                            </article>;
                        })}
                    </div>}
                </section>;
            })}
        <FloatingTools bankId={Number.isSafeInteger(initialBank) && initialBank > 0 ? initialBank : undefined} />
    </main>;
};
