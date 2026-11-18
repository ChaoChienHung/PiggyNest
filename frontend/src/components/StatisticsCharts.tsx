import { useState } from 'react';
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Legend, Pie, PieChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { useAuth } from '../context/useAuth';
import { useRates } from '../context/useRates';
import { useLedgerEntries } from '../context/useLedgerEntries';
import { asDateFormat, parseDate } from '../utils/dates';
import { convertLedger, summarizePeriods } from '../utils/ledgerAnalytics';
import { formatMoney } from '../utils/money';
import { rateSummary } from '../utils/currency';
import { ThemedSelect } from './ThemedSelect';
import { ExpenseCategoryChart } from './ExpenseCategoryChart';

interface StatisticsChartsProps {
    showAnalytics?: boolean;
    setShowAnalytics?: (show: boolean) => void;
    onOpenSettings?: () => void;
}

export const StatisticsCharts = ({ showAnalytics: visible, setShowAnalytics, onOpenSettings }: StatisticsChartsProps) => {
    const { user } = useAuth();
    const { rates, isLoading: ratesLoading } = useRates();
    const { banks, entries, loading, error } = useLedgerEntries();
    const [timeframe, setTimeframe] = useState<'month' | 'year'>('month');
    const [metric, setMetric] = useState<'balance' | 'flow'>('balance');
    const [selectedIds, setSelectedIds] = useState<number[] | null>(null);
    const [fromText, setFromText] = useState('');
    const [toText, setToText] = useState('');
    const [from, setFrom] = useState<string | null>(null);
    const [to, setTo] = useState<string | null>(null);
    const [internalVisible, setInternalVisible] = useState(false);
    const isVisible = visible ?? internalVisible;
    const hide = () => (setShowAnalytics ?? setInternalVisible)(false);
    const displayCurrency = user?.display_currency ?? 'NTD';
    const dateFormat = asDateFormat(user?.date_format);
    const selected = selectedIds ?? banks.map(bank => bank.id);
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
    const { converted, missing } = convertLedger(entries.filter(entry => selected.includes(entry.bank.id)), displayCurrency, rates);
    const { periods } = summarizePeriods(converted, timeframe, from, to);
    const categoryTotals: Record<string, number> = {};
    for (const row of periods) for (const [name, amount] of Object.entries(row.categoryExpenses)) {
        categoryTotals[name] = (categoryTotals[name] || 0) + amount;
    }
    const categoryData = Object.entries(categoryTotals).map(([name, value]) => ({ name, value }));
    const totalIncome = periods.reduce((sum, row) => sum + row.income, 0);
    const totalExpense = periods.reduce((sum, row) => sum + row.expense, 0);
    const flowData = [{ name: 'Income', value: totalIncome }, { name: 'Spending', value: totalExpense }].filter(item => item.value > 0);
    const ratesTitle = rateSummary(banks.filter(bank => selected.includes(bank.id)).map(bank => bank.currency), displayCurrency, rates);

    if (!isVisible) return null;
    if (loading || ratesLoading) return <div className="glass-panel p-6 mb-8 text-muted">Loading analytics…</div>;
    return <section className="glass-panel p-6 mb-8 animate-fade-in" aria-label="Financial analytics">
        <div className="analytics-heading">
            <h2 className="text-xl font-bold">Financial Analytics</h2>
            <div className="analytics-heading-actions">
                <ThemedSelect ariaLabel="Timeframe" className="analytics-select" value={timeframe}
                    onChange={value => setTimeframe(value as 'month' | 'year')}
                    options={[{ value: 'month', label: 'Monthly' }, { value: 'year', label: 'Yearly' }]} />
                <button type="button" className="btn btn-secondary" onClick={hide}>Hide</button>
            </div>
        </div>
        {error && <p role="alert" className="text-danger">{error}</p>}
        <div className="analytics-bank-filter" aria-label="PiggyBank filter">
            <span className="text-sm font-semibold">PiggyBanks</span>
            <button type="button" className="analytics-filter-action" onClick={() => setSelectedIds(banks.map(bank => bank.id))}>Select all</button>
            <button type="button" className="analytics-filter-action" onClick={() => setSelectedIds([])}>Clear all</button>
            <div className="analytics-bank-chips">
                {banks.map(bank => <label key={bank.id} className={`analytics-bank-chip${selected.includes(bank.id) ? ' is-selected' : ''}`}>
                    <input type="checkbox" checked={selected.includes(bank.id)} onChange={() => setSelectedIds(current => {
                        const values = current ?? banks.map(item => item.id);
                        return values.includes(bank.id) ? values.filter(id => id !== bank.id) : [...values, bank.id];
                    })} />
                    {bank.name} ({bank.currency})
                </label>)}
            </div>
        </div>
        <div className="analytics-date-filter">
            <label>From <input className="input-field" type="text" placeholder={dateFormat} value={fromText}
                onChange={event => applyRange(event.target.value, toText)} /></label>
            <label>To <input className="input-field" type="text" placeholder={dateFormat} value={toText}
                onChange={event => applyRange(fromText, event.target.value)} /></label>
            {rangeError && <span className="text-sm text-danger" role="alert">{rangeError}</span>}
        </div>
        {selected.length === 0 ? <p className="text-muted text-center p-8">Select a PiggyBank to see analytics.</p>
            : missing.length > 0 ? <p className="text-danger p-4">Rate needed for {missing.join(', ')}.{' '}
                <button type="button" className="networth-settings-link" onClick={onOpenSettings}>Open Settings</button>
            </p> : periods.length === 0 ? <p className="text-muted text-center p-8">No transactions in this date range.</p>
            : <>
                <div className="analytics-metric-tabs" role="group" aria-label="Chart metric">
                    <button type="button" className={`btn ${metric === 'balance' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setMetric('balance')}>Balance</button>
                    <button type="button" className={`btn ${metric === 'flow' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setMetric('flow')}>Income and spending</button>
                </div>
                <div className="analytics-chart" role="img" aria-label={`${metric === 'balance' ? 'Combined balance' : 'Combined income and spending'} in ${displayCurrency}`} title={ratesTitle}>
                    <ResponsiveContainer width="100%" height="100%">
                        {metric === 'balance' ? <AreaChart data={periods} margin={{ top: 20, right: 20, left: 5, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="4 4" stroke="rgba(255,141,161,.15)" />
                            <XAxis dataKey="period" /><YAxis /><Tooltip formatter={(value) => formatMoney(Number(value), displayCurrency)} />
                            <Area type="stepAfter" dataKey="balance" name="Balance" stroke="#ff8da1" fill="#ffe5ea" />
                        </AreaChart> : <BarChart data={periods} margin={{ top: 20, right: 20, left: 5, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="4 4" stroke="rgba(255,141,161,.15)" />
                            <XAxis dataKey="period" /><YAxis /><Tooltip formatter={(value) => formatMoney(Number(value), displayCurrency)} /><Legend />
                            <Bar dataKey="income" name="Income" fill="#ffd166" /><Bar dataKey="expense" name="Spending" fill="#ff8da1" />
                        </BarChart>}
                    </ResponsiveContainer>
                </div>
                <div className="analytics-summary">
                    <p>Ending balance: <strong title={ratesTitle}>{formatMoney(periods[periods.length - 1].balance, displayCurrency)}</strong></p>
                    <p>Income: <strong title={ratesTitle}>{formatMoney(totalIncome, displayCurrency)}</strong></p>
                    <p>Spending: <strong title={ratesTitle}>{formatMoney(totalExpense, displayCurrency)}</strong></p>
                </div>
                <div className="analytics-pies">
                    {flowData.length > 0 && <div>
                        <h3 className="text-center font-semibold mb-4 text-text-secondary">Overall Money Flow</h3>
                        <div className="analytics-pie-chart"><ResponsiveContainer width="100%" height="100%">
                            <PieChart><Pie data={flowData} dataKey="value" cx="50%" cy="50%" innerRadius={55} outerRadius={80}>
                                {flowData.map(item => <Cell key={item.name} fill={item.name === 'Income' ? '#ffd166' : '#ff8da1'} />)}
                            </Pie><Tooltip formatter={(value) => formatMoney(Number(value), displayCurrency)} /><Legend /></PieChart>
                        </ResponsiveContainer></div>
                    </div>}
                    {categoryData.length > 0 && <ExpenseCategoryChart data={categoryData} currency={displayCurrency} />}
                </div>
            </>}
    </section>;
};
