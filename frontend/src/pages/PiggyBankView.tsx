import React, { useEffect, useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { piggybanksApi } from '../api/piggybanks';
import { transactionsApi } from '../api/transactions';
import { categoriesApi } from '../api/categories';
import type { Transaction, PiggyBank, Balance, Category } from '../types';
import { ArrowLeft, ArrowUpRight, ArrowDownRight, ArrowRight, Plus, Pencil, ChevronLeft, ChevronRight } from 'lucide-react';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { ConfirmModal, type ModalVariant } from '../components/ConfirmModal';
import { FloatingTools } from '../components/FloatingTools';
import { ThemedSelect } from '../components/ThemedSelect';
import { SettingsDialog } from '../components/SettingsDialog';
import { ExpenseCategoryChart } from '../components/ExpenseCategoryChart';
import { DateTextField } from '../components/DateTextField';
import { formatMoney } from '../utils/money';
import { useAuth } from '../context/useAuth';
import { useRates } from '../context/useRates';
import { convertAmount } from '../utils/currency';
import { asDateFormat, formatDate, isoDatePart, parseDate, todayIsoDate } from '../utils/dates';

const transferNote = (description?: string) => {
    const note = description || '';
    const separator = note.indexOf(': ');
    return separator >= 0 ? note.slice(separator + 2) : note;
};

/**
 * Dedicated view for a single PiggyBank account.
 * Handles fetching specific nested transactions and managing the dynamic "Add Transaction" form logic.
 */
export const PiggyBankView = () => {
    const { id } = useParams<{ id: string }>();
    const [bank, setBank] = useState<PiggyBank | null>(null);
    const [balance, setBalance] = useState<Balance | null>(null);
    const [transactions, setTransactions] = useState<Transaction[]>([]);

    // For transfer form
    const [allBanks, setAllBanks] = useState<PiggyBank[]>([]);
    const [categories, setCategories] = useState<Category[]>([]);

    const [isLoading, setIsLoading] = useState(true);
    const [showAnalytics, setShowAnalytics] = useState(false);
    const [settingsOpen, setSettingsOpen] = useState(false);
    const settingsButtonRef = React.useRef<HTMLButtonElement>(null);
    const [lineMetric, setLineMetric] = useState<'balance' | 'income' | 'expense'>('balance');

    // Form states
    const [showAdd, setShowAdd] = useState(false);
    const [editingTxId, setEditingTxId] = useState<number | null>(null);
    const { user } = useAuth();
    const { rates, isLoading: ratesLoading } = useRates();
    const dateFormat = asDateFormat(user?.date_format);
    // 0 means show every transaction on one page.
    const pageSize = user?.transactions_per_page ?? 20;
    const [page, setPage] = useState(1);
    const [pageInput, setPageInput] = useState('');
    const [pageError, setPageError] = useState('');
    const [sortField, setSortField] = useState<'date' | 'amount'>('date');
    const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
    const [categoryFilters, setCategoryFilters] = useState<string[]>([]);
    const categoryFilterRef = React.useRef<HTMLDetailsElement>(null);
    const [dateFromText, setDateFromText] = useState('');
    const [dateToText, setDateToText] = useState('');
    const [appliedFrom, setAppliedFrom] = useState<string | null>(null);
    const [appliedTo, setAppliedTo] = useState<string | null>(null);
    const editingTransaction = transactions.find(tx => tx.id === editingTxId);
    const [amount, setAmount] = useState('');
    const [type, setType] = useState('expense');
    const [desc, setDesc] = useState('');
    // Holds the date as typed, in the user's chosen format.
    const [txDate, setTxDate] = useState(() => formatDate(todayIsoDate(), dateFormat));

    // Category states
    const [selectedCatId, setSelectedCatId] = useState('');
    const [newCatName, setNewCatName] = useState('');
    const [isCreatingCat, setIsCreatingCat] = useState(false);

    // Transfer states
    const [targetBankId, setTargetBankId] = useState('');
    const [otherAmount, setOtherAmount] = useState('');
    const [transferPair, setTransferPair] = useState<{ debit: Transaction; credit: Transaction } | null>(null);

    // Modal state
    const [modalOpen, setModalOpen] = useState(false);
    const [modalConfig, setModalConfig] = useState<{
        title: string; message: string; variant: ModalVariant;
        confirmText?: string; alertOnly?: boolean;
        onConfirm: () => void;
    }>({ title: '', message: '', variant: 'info', onConfirm: () => {} });

    const showModal = useCallback((cfg: typeof modalConfig & { alertOnly?: boolean }) => {
        setModalConfig(cfg);
        setModalOpen(true);
    }, []);
    const closeModal = useCallback(() => setModalOpen(false), []);

    const changeDateRange = (fromText: string, toText: string) => {
        setDateFromText(fromText);
        setDateToText(toText);
        const from = fromText.trim() ? parseDate(fromText, dateFormat) : null;
        const to = toText.trim() ? parseDate(toText, dateFormat) : null;
        if ((!fromText.trim() || from) && (!toText.trim() || to) && (!from || !to || from <= to)) {
            setAppliedFrom(from);
            setAppliedTo(to);
            setPage(1);
        }
    };

    /**
     * Re-fetches all critical data relating to this specific PiggyBank.
     * Grabs underlying transactions, current balance totals, and external categories/PiggyBanks for dropdowns.
     * A silent refresh keeps the current page rendered, so saving or deleting
     * a transaction does not replace the list with a loader and reset scroll.
     */
    const loadData = useCallback(async ({ silent = false }: { silent?: boolean } = {}) => {
        if (!id) return;
        if (!silent) setIsLoading(true);
        try {
            const pbs = await piggybanksApi.list();
            setAllBanks(pbs);
            const currentBank = pbs.find((p: PiggyBank) => p.id === parseInt(id));
            setBank(currentBank || null);

            const bal = await piggybanksApi.getBalance(parseInt(id));
            setBalance(bal);

            const txs = await transactionsApi.list(parseInt(id));
            setTransactions(txs);

            const cats = await categoriesApi.list();
            setCategories(cats);
        } catch (err) {
            console.error("Failed to load info", err);
        } finally {
            setIsLoading(false);
        }
    }, [id]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    useEffect(() => {
        const closeOutside = (event: PointerEvent) => {
            if (categoryFilterRef.current && !categoryFilterRef.current.contains(event.target as Node)) {
                categoryFilterRef.current.open = false;
            }
        };
        const closeEscape = (event: KeyboardEvent) => {
            if (event.key === 'Escape' && categoryFilterRef.current?.open) {
                categoryFilterRef.current.open = false;
                categoryFilterRef.current.querySelector<HTMLElement>('summary')?.focus();
            }
        };
        document.addEventListener('pointerdown', closeOutside);
        document.addEventListener('keydown', closeEscape);
        return () => {
            document.removeEventListener('pointerdown', closeOutside);
            document.removeEventListener('keydown', closeEscape);
        };
    }, []);

    /**
     * Primary form submission handler for injecting new transactions.
     * Evaluates whether it's an Income/Expense/Transfer, processes category creation,
     * and finally uploads everything via the `transactionsApi`.
     */
    const handleAddTx = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!id) return;

        let finalAmount = parseFloat(amount);
        if (['expense', 'withdrawal', 'transfer_out'].includes(type)) finalAmount = -Math.abs(finalAmount);
        if (['income', 'deposit', 'transfer_in'].includes(type)) finalAmount = Math.abs(finalAmount);

        const isoDate = parseDate(txDate, dateFormat);
        if (!isoDate) {
            showModal({ title: 'Check the date', message: `Enter a real date in the format ${dateFormat}.`, variant: 'warning', alertOnly: true, onConfirm: closeModal });
            return;
        }

        try {
            // First resolve category
            let finalCategoryName = '';
            if (type !== 'transfer' && isCreatingCat && newCatName.trim() !== '') {
                const newCat = await categoriesApi.create(newCatName.trim());
                finalCategoryName = newCat.name;
            } else if (selectedCatId === 'CURRENT') {
                finalCategoryName = editingTransaction?.category || '';
            } else if (selectedCatId) {
                const cat = categories.find(c => c.id.toString() === selectedCatId);
                if (cat) finalCategoryName = cat.name;
            }

            if (editingTxId !== null) {
                let finalDate = undefined;
                if (isoDate) {
                    finalDate = `${isoDate}T00:00:00`;
                }
                if (editingTransaction?.type === 'transfer') {
                    const signedAmount = editingTransaction.amount < 0 ? -Math.abs(finalAmount) : Math.abs(finalAmount);
                    await transactionsApi.update(editingTxId, {
                        amount: signedAmount,
                        counterpart_amount: isCrossCurrencyEdit ? parseFloat(otherAmount) : undefined,
                        description: desc, date: finalDate,
                    });
                } else {
                    await transactionsApi.update(editingTxId, {
                        amount: finalAmount, type, description: desc,
                        category: finalCategoryName, date: finalDate,
                    });
                }
            } else if (type === 'transfer') {
                if (!targetBankId) {
                    showModal({ title: 'Missing Target', message: 'Please select a target Piggy Bank for transfer.', variant: 'warning', alertOnly: true, onConfirm: closeModal });
                    return;
                }
                const amt = Math.abs(parseFloat(amount));
                await transactionsApi.transfer(
                    parseInt(id), parseInt(targetBankId), amt, desc,
                    isCrossCurrencyCreate ? parseFloat(otherAmount) : undefined,
                    `${isoDate}T00:00:00`,
                );
            } else {
                let finalDate = undefined;
                if (isoDate) {
                    finalDate = `${isoDate}T00:00:00`;
                }
                await transactionsApi.create(parseInt(id), finalAmount, type, desc, finalCategoryName, finalDate);
            }

            setShowAdd(false);
            setAmount('');
            setOtherAmount('');
            setTransferPair(null);
            setDesc('');
            setSelectedCatId('');
            setNewCatName('');
            setIsCreatingCat(false);
            setType('expense');
            setTxDate(formatDate(todayIsoDate(), dateFormat));
            setEditingTxId(null);
            await loadData({ silent: true });
        } catch (err) {
            console.error("Failed to save transaction", err);
            showModal({ title: 'Oops!', message: 'Failed to save transaction. Please try again.', variant: 'danger', alertOnly: true, onConfirm: closeModal });
        }
    };

    if (isLoading) return <div className="p-8 text-center text-muted animate-fade-in">Loading...</div>;
    if (!bank) return <div className="p-8 text-center text-danger animate-fade-in">PiggyBank not found.</div>;

    const parsedFrom = dateFromText.trim() ? parseDate(dateFromText, dateFormat) : null;
    const parsedTo = dateToText.trim() ? parseDate(dateToText, dateFormat) : null;
    const dateRangeError = dateFromText.trim() && !parsedFrom ? `Start date must use ${dateFormat}.`
        : dateToText.trim() && !parsedTo ? `End date must use ${dateFormat}.`
        : parsedFrom && parsedTo && parsedFrom > parsedTo ? 'Start date must be on or before end date.' : '';
    const inDateRange = (tx: Transaction) => {
        const day = isoDatePart(tx.date);
        return (!appliedFrom || day >= appliedFrom) && (!appliedTo || day <= appliedTo);
    };
    const matchingTransactions = transactions.filter(tx =>
        inDateRange(tx) && (categoryFilters.length === 0 || categoryFilters.includes(tx.category || ''))
    ).sort((a, b) => {
        const result = sortField === 'date'
            ? isoDatePart(a.date).localeCompare(isoDatePart(b.date))
            : a.amount - b.amount;
        return (sortDirection === 'asc' ? result : -result) || b.id - a.id;
    });
    const totalPages = pageSize > 0 ? Math.max(1, Math.ceil(matchingTransactions.length / pageSize)) : 1;
    // Deleting the last row of the final page leaves the user on the new last page.
    const currentPage = Math.min(page, totalPages);
    const pageWindowStart = Math.min(currentPage, Math.max(1, totalPages - 4));
    const pageWindowEnd = Math.min(totalPages, pageWindowStart + 4);
    const nearbyPages = Array.from({ length: pageWindowEnd - pageWindowStart + 1 }, (_, index) => pageWindowStart + index);
    const goToPage = (target: number) => {
        setPage(target);
        setPageError('');
        setPageInput('');
    };
    const visibleTransactions = pageSize > 0
        ? matchingTransactions.slice((currentPage - 1) * pageSize, currentPage * pageSize)
        : matchingTransactions;
    const firstShown = matchingTransactions.length === 0 ? 0 : (currentPage - 1) * (pageSize || matchingTransactions.length) + 1;
    const lastShown = firstShown + visibleTransactions.length - 1;
    const filterCategories = [...new Set(transactions.map(tx => tx.category || ''))].sort((a, b) => a.localeCompare(b));
    const analyticsTransactions = transactions.filter(inDateRange);

    const transferTargets = allBanks.filter(b => b.id !== bank.id);
    const displayCurrency = user?.display_currency ?? 'NTD';
    const convertedBalance = convertAmount(balance?.balance ?? 0, bank.currency, displayCurrency, rates);
    const targetBank = allBanks.find(b => b.id === Number(targetBankId));
    const isCrossCurrencyCreate = type === 'transfer' && editingTxId === null && !!targetBank && targetBank.currency !== bank.currency;
    const counterpart = transferPair && editingTxId !== null
        ? (transferPair.debit.id === editingTxId ? transferPair.credit : transferPair.debit)
        : null;
    const counterpartBank = allBanks.find(b => b.id === counterpart?.piggy_bank_id);
    const isCrossCurrencyEdit = type === 'transfer' && editingTxId !== null && !!counterpartBank && counterpartBank.currency !== bank.currency;
    const hasOtherAmount = isCrossCurrencyCreate || isCrossCurrencyEdit;
    const editingCredit = editingTxId !== null && (editingTransaction?.amount ?? 0) > 0;
    const sourceCurrency = editingCredit ? counterpartBank?.currency : bank.currency;
    const receivedCurrency = editingCredit ? bank.currency : (targetBank?.currency || counterpartBank?.currency);
    const sentValue = editingCredit ? Number(otherAmount) : Number(amount);
    const receivedValue = editingCredit ? Number(amount) : Number(otherAmount);
    const impliedRate = hasOtherAmount && sentValue > 0 && receivedValue > 0
        ? receivedValue / sentValue : null;

    // One point per calendar day: the end-of-day balance plus that day's money in and out.
    // `t` is UTC midnight of the date, so the time axis spaces days evenly in any time zone.
    const dailyTotals = new Map<string, { income: number; expense: number; net: number }>();
    for (const tx of analyticsTransactions) {
        const day = isoDatePart(tx.date);
        const totals = dailyTotals.get(day) ?? { income: 0, expense: 0, net: 0 };
        if (tx.type !== 'transfer') {
            if (tx.amount > 0) totals.income += tx.amount;
            else totals.expense += Math.abs(tx.amount);
        }
        totals.net += tx.amount;
        dailyTotals.set(day, totals);
    }
    let runningBalance = appliedFrom
        ? transactions.filter(tx => isoDatePart(tx.date) < appliedFrom).reduce((sum, tx) => sum + tx.amount, 0)
        : 0;
    const lineChartData = [...dailyTotals.entries()]
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([day, totals]) => {
            runningBalance += totals.net;
            const [y, m, d] = day.split('-').map(Number);
            return {
                t: Date.UTC(y, m - 1, d),
                day,
                balance: Math.round(runningBalance * 100) / 100,
                income: Math.round(totals.income * 100) / 100,
                expense: Math.round(totals.expense * 100) / 100,
            };
        });

    // Tick at the start of each month in range, thinned to at most ~8 labels.
    const monthTicks: number[] = [];
    if (lineChartData.length > 0) {
        const first = new Date(lineChartData[0].t);
        const last = lineChartData[lineChartData.length - 1].t;
        for (let y = first.getUTCFullYear(), m = first.getUTCMonth() + 1; ; m++) {
            if (m > 11) { y++; m = 0; }
            const tick = Date.UTC(y, m, 1);
            if (tick > last) break;
            monthTicks.push(tick);
        }
    }
    const tickStep = Math.max(1, Math.ceil(monthTicks.length / 8));
    const xTicks = monthTicks.length >= 2 ? monthTicks.filter((_, i) => i % tickStep === 0) : undefined;
    const formatMonthTick = (t: number) => {
        const date = new Date(t);
        return xTicks
            ? `${date.getUTCFullYear()}/${String(date.getUTCMonth() + 1).padStart(2, '0')}`
            : formatDate(new Date(t).toISOString(), dateFormat);
    };
    const lineColor = lineMetric === 'expense' ? '#ff8da1' : '#f4b740';

    // Group monthly for Bar Chart
    const monthlyTotals: Record<string, { month: string, income: number, expense: number }> = {};
    analyticsTransactions.forEach(tx => {
        const date = new Date(tx.date);
        const monthStr = date.toLocaleDateString(undefined, { year: 'numeric', month: 'short' });
        if (!monthlyTotals[monthStr]) {
            monthlyTotals[monthStr] = { month: monthStr, income: 0, expense: 0 };
        }
        if (tx.type === 'transfer') return;
        if (tx.amount > 0) {
            monthlyTotals[monthStr].income += tx.amount;
        } else {
            monthlyTotals[monthStr].expense += Math.abs(tx.amount);
        }
    });
    const barData = Object.values(monthlyTotals).reverse();

    // Group category totals for Pie Chart
    const catTotals: Record<string, number> = {};
    analyticsTransactions.forEach(tx => {
        if (tx.type !== 'transfer' && tx.amount < 0 && tx.category) {
            catTotals[tx.category] = (catTotals[tx.category] || 0) + Math.abs(tx.amount);
        }
    });
    const pieData = Object.entries(catTotals)
        .map(([name, value]) => ({ name, value }))
        .filter(d => d.value > 0)
        .sort((a, b) => b.value - a.value);

    const transactionForm = (
        <form
            id={editingTxId !== null ? `transaction-editor-${editingTxId}` : 'transaction-add-form'}
            onSubmit={handleAddTx}
            className="glass-panel p-6 mb-8 animate-fade-in flex flex-col gap-4 transaction-form"
        >
            <h3 className="text-lg font-semibold mb-2">{editingTxId ? 'Edit Transaction' : 'Add New Transaction'}</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
                <div>
                    <label htmlFor="transaction-type" className="block text-sm font-medium text-text-secondary mb-1">Type</label>
                    <ThemedSelect
                        id="transaction-type"
                        className="transaction-compact-select"
                        value={type}
                        onChange={setType}
                        disabled={editingTransaction?.type === 'transfer'}
                        options={[
                            { value: 'expense', label: 'Expense' },
                            { value: 'income', label: 'Income' },
                            { value: 'withdrawal', label: 'Withdrawal' },
                            { value: 'deposit', label: 'Deposit' },
                            { value: 'transfer_out', label: 'Bank Transfer Out' },
                            { value: 'transfer_in', label: 'Bank Transfer In' },
                            ...(editingTxId === null || type === 'transfer' ? [{ value: 'transfer', label: 'PiggyBank Transfer' }] : []),
                        ]}
                    />
                </div>

                <DateTextField id="transaction-date" label={`Date (${dateFormat})`} value={txDate}
                    onChange={setTxDate} dateFormat={dateFormat} required />

                {type === 'transfer' && editingTxId === null && (
                    <div>
                        <label className="block text-sm font-medium text-text-secondary mb-1">Transfer To</label>
                        <ThemedSelect
                            ariaLabel="Transfer To"
                            value={targetBankId}
                            onChange={(value) => { setTargetBankId(value); setOtherAmount(''); }}
                            options={[
                                { value: '', label: 'Select PiggyBank...' },
                                ...transferTargets.map(t => ({ value: String(t.id), label: t.name })),
                            ]}
                        />
                    </div>
                )}

                <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1">
                        {type === 'transfer'
                            ? `${editingTransaction?.amount && editingTransaction.amount > 0 ? 'Amount Received' : 'Amount Sent'} (${bank.currency})`
                            : 'Amount'}
                    </label>
                    <input
                        type="number"
                        step="0.01"
                        required
                        min="0.01"
                        className="input-field"
                        value={amount}
                        onChange={(e) => setAmount(e.target.value)}
                        placeholder="0.00"
                    />
                </div>

                {hasOtherAmount && (
                    <div>
                        <label className="block text-sm font-medium text-text-secondary mb-1">
                            {isCrossCurrencyCreate || (editingTransaction?.amount ?? -1) < 0 ? 'Amount Received' : 'Amount Sent'} ({(targetBank || counterpartBank)?.currency})
                        </label>
                        <input
                            type="number"
                            step="0.01"
                            min="0.01"
                            required
                            className="input-field"
                            value={otherAmount}
                            onChange={(e) => setOtherAmount(e.target.value)}
                            placeholder="0.00"
                        />
                    </div>
                )}

                {impliedRate !== null && (
                    <p className="text-sm text-muted md:col-span-2" role="status">
                        1 {sourceCurrency} ≈ {impliedRate.toFixed(4)} {receivedCurrency}
                    </p>
                )}

                {type !== 'transfer' && (
                    <div>
                        <label htmlFor={isCreatingCat ? 'new-category' : 'transaction-category'} className="block text-sm font-medium text-text-secondary mb-1">Category</label>
                        {isCreatingCat ? (
                            <div className="flex gap-2">
                                <input
                                    id="new-category"
                                    type="text"
                                    className="input-field flex-1"
                                    value={newCatName}
                                    onChange={(e) => setNewCatName(e.target.value)}
                                    placeholder="New Category..."
                                    autoFocus
                                />
                                <button type="button" onClick={() => setIsCreatingCat(false)} className="btn btn-secondary px-3 text-xs">
                                    Cancel
                                </button>
                            </div>
                        ) : (
                            <ThemedSelect
                                id="transaction-category"
                                className="transaction-compact-select"
                                value={selectedCatId}
                                onChange={(value) => {
                                    if (value === 'NEW') setIsCreatingCat(true);
                                    else setSelectedCatId(value);
                                }}
                                options={[
                                    { value: '', label: 'No Category' },
                                    ...(editingTransaction?.category && !categories.some(c => c.name === editingTransaction.category)
                                        ? [{ value: 'CURRENT', label: `${editingTransaction.category} (current)` }] : []),
                                    ...categories.map(c => ({ value: String(c.id), label: c.name })),
                                    { value: 'NEW', label: 'Create New Category' },
                                ]}
                            />
                        )}
                    </div>
                )}

                <div className={type === 'transfer' ? "md:col-span-2" : ""}>
                    <label className="block text-sm font-medium text-text-secondary mb-1">{type === 'transfer' ? 'Transfer Note' : 'Description'}</label>
                    <input
                        type="text"
                        className="input-field"
                        value={desc}
                        onChange={(e) => setDesc(e.target.value)}
                        placeholder="Optional notes"
                    />
                </div>
            </div>
            <div className="flex justify-end gap-3 mt-2">
                <button
                    type="button"
                    onClick={() => {
                        setShowAdd(false);
                        setAmount('');
                        setOtherAmount('');
                        setTransferPair(null);
                        setDesc('');
                        setSelectedCatId('');
                        setNewCatName('');
                        setIsCreatingCat(false);
                        setType('expense');
                        setTxDate(formatDate(todayIsoDate(), dateFormat));
                        setEditingTxId(null);
                    }}
                    className="btn btn-secondary text-sm"
                >
                    Cancel
                </button>
                <button type="submit" className="btn btn-primary text-sm">
                    {editingTxId ? 'Save Changes' : 'Save Transaction'}
                </button>
            </div>
        </form>
    );

    return (
        <div className="container page-layout-container animate-fade-in">
            <div className="piggybank-page-header">
                <Link to="/" className="back-to-dashboard-link">
                    <ArrowLeft size={16} className="mr-2" /> Back to Dashboard
                </Link>
                <div className="piggybank-header-actions">
                    <Link to={`/reports?bank=${bank.id}`} className="btn btn-secondary">Reports</Link>
                    <button ref={settingsButtonRef} type="button" className="btn btn-secondary" onClick={() => setSettingsOpen(true)}>Settings</button>
                </div>
            </div>

            <div className="glass-panel balance-card mb-8">
                <div className="balance-card-header">
                    <h1 className="balance-card-title">{bank.name}</h1>
                    <p className="balance-card-subtitle">PiggyBank Details & Savings Nest</p>
                </div>

                <div className="balance-card-divider" />

                <div className="balance-card-body">
                    <p className="balance-card-label">Current Balance</p>
                    <h2 className="balance-card-amount">
                        {formatMoney(balance?.balance ?? 0, bank.currency)}
                    </h2>
                    {bank.currency !== displayCurrency && <p className="text-sm text-text-secondary" title={convertedBalance?.updatedAt
                        ? `${convertedBalance.explanation}; set ${convertedBalance.updatedAt}` : undefined}>
                        {ratesLoading ? 'Loading rate…' : convertedBalance
                            ? `≈ ${formatMoney(convertedBalance.amount, displayCurrency)}`
                            : <button type="button" className="networth-settings-link" onClick={() => setSettingsOpen(true)}>Rate needed — open Settings</button>}
                    </p>}
                </div>
            </div>

            <div className="transaction-section-header flex justify-between items-center mb-6">
                <h2 className="transactions-section-title">Transactions</h2>
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => {
                            if (showAdd && editingTxId !== null) {
                                setAmount('');
                                setDesc('');
                                setSelectedCatId('');
                                setNewCatName('');
                                setIsCreatingCat(false);
                                setType('expense');
                                setTxDate(formatDate(todayIsoDate(), dateFormat));
                                setEditingTxId(null);
                            } else {
                                setShowAdd(!showAdd);
                            }
                        }}
                        className="btn btn-primary"
                    >
                        <Plus size={16} /> Add Transaction
                    </button>
                </div>
            </div>

            {showAdd && editingTxId === null && transactionForm}

            <div className="glass-panel transaction-filter-panel mb-8">
                <div className="transaction-filter-grid">
                    <div>
                        <label htmlFor="transaction-sort" className="text-sm font-medium text-text-secondary">Sort by</label>
                        <ThemedSelect
                            id="transaction-sort"
                            value={sortField}
                            onChange={(value) => { setSortField(value as 'date' | 'amount'); setPage(1); }}
                            options={[{ value: 'date', label: 'Date' }, { value: 'amount', label: 'Amount' }]}
                        />
                    </div>
                    <div>
                        <label htmlFor="transaction-direction" className="text-sm font-medium text-text-secondary">Order</label>
                        <ThemedSelect
                            id="transaction-direction"
                            value={sortDirection}
                            onChange={(value) => { setSortDirection(value as 'asc' | 'desc'); setPage(1); }}
                            options={[{ value: 'desc', label: 'Descending' }, { value: 'asc', label: 'Ascending' }]}
                        />
                    </div>
                    <details ref={categoryFilterRef} className="transaction-category-filter">
                        <summary>Categories{categoryFilters.length ? ` (${categoryFilters.length})` : ' (all)'}</summary>
                        <div className="transaction-category-options">
                            {filterCategories.length ? filterCategories.map(category => (
                                <label key={category || 'uncategorized'}>
                                    <input
                                        type="checkbox"
                                        checked={categoryFilters.includes(category)}
                                        onChange={(event) => {
                                            setCategoryFilters(current => event.target.checked
                                                ? [...current, category]
                                                : current.filter(item => item !== category));
                                            setPage(1);
                                        }}
                                    />
                                    {category || 'Uncategorized'}
                                </label>
                            )) : <p className="text-muted text-sm">No categories yet.</p>}
                        </div>
                    </details>
                    <DateTextField id="filter-date-from" label={`From (${dateFormat})`} value={dateFromText}
                        onChange={value => changeDateRange(value, dateToText)} dateFormat={dateFormat} invalid={!!dateRangeError} />
                    <DateTextField id="filter-date-to" label={`To (${dateFormat})`} value={dateToText}
                        onChange={value => changeDateRange(dateFromText, value)} dateFormat={dateFormat} invalid={!!dateRangeError} />
                </div>
                {dateRangeError && <p className="text-sm text-danger" role="alert">{dateRangeError} The previous valid range remains applied.</p>}
                <div className="transaction-filter-footer">
                    <p className="text-sm text-muted">{matchingTransactions.length} matching transactions. Date range also applies to analytics.</p>
                    <button type="button" className="btn btn-secondary text-sm" onClick={() => {
                        setSortField('date');
                        setSortDirection('desc');
                        setCategoryFilters([]);
                        setDateFromText('');
                        setDateToText('');
                        setAppliedFrom(null);
                        setAppliedTo(null);
                        setPage(1);
                    }}>Clear filters</button>
                </div>
            </div>

            {showAnalytics && (
                <div className="glass-panel p-6 mb-8 animate-fade-in">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-xl font-bold">PiggyBank Analytics</h3>
                        <div className="flex gap-4 items-center">
                            <ThemedSelect
                                ariaLabel="Analytics metric"
                                className="analytics-select"
                                value={lineMetric}
                                onChange={(value) => setLineMetric(value as 'balance' | 'income' | 'expense')}
                                options={[
                                    { value: 'balance', label: 'Running Balance' },
                                    { value: 'income', label: 'Income / Deposits' },
                                    { value: 'expense', label: 'Expenses / Withdrawals' },
                                ]}
                            />

                            <button
                                onClick={() => setShowAnalytics(false)}
                                className="text-muted hover:text-text-primary text-sm font-semibold transition-colors"
                                style={{ border: 'none', background: 'transparent', cursor: 'pointer', outline: 'none', padding: 0 }}
                            >
                                Hide
                            </button>
                        </div>
                    </div>

                    <div style={{ height: '300px', width: '100%' }} className="mb-8">
                        {lineChartData.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart
                                    data={lineChartData}
                                    margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                                >
                                    <defs>
                                        <linearGradient id="analytics-area-fill" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%" stopColor={lineColor} stopOpacity={0.28} />
                                            <stop offset="100%" stopColor={lineColor} stopOpacity={0.02} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="4 4" stroke="rgba(255, 141, 161, 0.15)" vertical={false} />
                                    <XAxis
                                        dataKey="t"
                                        type="number"
                                        scale="time"
                                        domain={['dataMin', 'dataMax']}
                                        ticks={xTicks}
                                        tickFormatter={formatMonthTick}
                                        minTickGap={24}
                                        stroke="#8c768f"
                                        style={{ fontSize: '0.85rem', fontWeight: 600 }}
                                    />
                                    <YAxis stroke="#8c768f" style={{ fontSize: '0.85rem', fontWeight: 600 }} width={56} />
                                    <Tooltip
                                        labelFormatter={(t) => formatDate(new Date(Number(t)).toISOString(), dateFormat)}
                                        formatter={(value) => formatMoney(Number(value), bank.currency)}
                                        contentStyle={{ 
                                            backgroundColor: 'rgba(255, 255, 255, 0.95)', 
                                            border: '2px solid rgba(255, 141, 161, 0.2)', 
                                            borderRadius: '16px',
                                            boxShadow: '0 8px 24px rgba(255, 141, 161, 0.1)',
                                            color: '#4a3e4b'
                                        }}
                                    />
                                    <Legend wrapperStyle={{ paddingTop: '10px' }} />
                                    <Area
                                        type={lineMetric === 'balance' ? 'stepAfter' : 'monotone'}
                                        dataKey={lineMetric}
                                        name={
                                            lineMetric === 'balance' ? 'Running Balance' :
                                            lineMetric === 'income' ? 'Income / Deposits' :
                                            'Expenses / Withdrawals'
                                        }
                                        stroke={lineColor}
                                        strokeWidth={2.5}
                                        fill="url(#analytics-area-fill)"
                                        dot={false}
                                        activeDot={{ r: 5, strokeWidth: 2, stroke: '#fff', fill: lineColor }}
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="flex items-center justify-center h-full text-muted">
                                No transaction data available for graphing.
                            </div>
                        )}
                    </div>

                    {lineChartData.length > 0 && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 border-t border-glass-border pt-8 mt-4">
                            {/* Bar Chart: Monthly Summary */}
                            <div>
                                <h4 className="text-center font-semibold mb-4 text-text-secondary">Monthly Summary</h4>
                                <div style={{ height: '250px', width: '100%' }}>
                                    {barData.length > 0 ? (
                                        <ResponsiveContainer width="100%" height="100%">
                                            <BarChart
                                                data={barData}
                                                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                                            >
                                                <CartesianGrid strokeDasharray="4 4" stroke="rgba(255, 141, 161, 0.15)" />
                                                <XAxis dataKey="month" stroke="#8c768f" style={{ fontSize: '0.8rem', fontWeight: 600 }} />
                                                <YAxis stroke="#8c768f" style={{ fontSize: '0.8rem', fontWeight: 600 }} />
                                                <Tooltip
                                                    cursor={{ fill: 'rgba(255, 141, 161, 0.05)' }}
                                                    contentStyle={{ 
                                                        backgroundColor: 'rgba(255, 255, 255, 0.95)', 
                                                        border: '2px solid rgba(255, 141, 161, 0.2)', 
                                                        borderRadius: '16px',
                                                        color: '#4a3e4b'
                                                    }}
                                                />
                                                <Legend />
                                                <Bar dataKey="income" name="Income/Deposits" fill="#ffd166" radius={[6, 6, 0, 0]} maxBarSize={35} />
                                                <Bar dataKey="expense" name="Expenses/Withdrawals" fill="#ff8da1" radius={[6, 6, 0, 0]} maxBarSize={35} />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    ) : (
                                        <div className="flex h-full items-center justify-center text-muted text-sm pb-8">No monthly flow data yet.</div>
                                    )}
                                </div>
                            </div>

                            {/* Pie Chart: Expense Breakdown by Category */}
                            <div>
                                <ExpenseCategoryChart data={pieData} currency={bank.currency} />
                            </div>
                        </div>
                    )}
                </div>
            )}

            <div className="glass-panel transaction-table-panel">
                {matchingTransactions.length === 0 ? (
                    <div className="p-8 text-center text-muted">{transactions.length ? 'No transactions match these filters.' : 'No transactions found.'}</div>
                ) : (
                    <table className="w-full text-left border-collapse transaction-table">
                        <thead>
                            <tr className="border-b border-glass-border">
                                <th className="p-4 text-text-secondary font-medium">Date</th>
                                <th className="p-4 text-text-secondary font-medium">Type</th>
                                <th className="p-4 text-text-secondary font-medium">Category</th>
                                <th className="p-4 text-text-secondary font-medium">Description</th>
                                <th className="p-4 text-text-secondary font-medium text-right">Amount</th>
                                <th className="p-4 text-text-secondary font-medium text-center">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {visibleTransactions.map((tx) => {
                                const isIncome = tx.amount > 0 && !['transfer', 'transfer_in', 'transfer_out'].includes(tx.type);
                                const isTransfer = ['transfer', 'transfer_in', 'transfer_out'].includes(tx.type);

                                let icon = <ArrowDownRight size={14} className="mr-1" />;
                                let typeLabel = 'Expense';
                                let badgeClass = 'bg-danger bg-opacity-10 text-danger';
                                let textClass = 'text-danger';

                                if (isIncome) {
                                    icon = <ArrowUpRight size={14} className="mr-1" />;
                                    typeLabel = 'Income';
                                    badgeClass = 'bg-success bg-opacity-10 text-success';
                                    textClass = 'text-success';
                                } else if (isTransfer) {
                                    icon = <ArrowRight size={14} className="mr-1" />;
                                    typeLabel = tx.type === 'transfer_out' ? 'Bank Transfer Out' : tx.type === 'transfer_in' ? 'Bank Transfer In' : 'PiggyBank Transfer';
                                    badgeClass = 'bg-accent-light text-accent-primary';
                                    if (tx.amount > 0) {
                                        textClass = 'text-success';
                                    } else {
                                        textClass = 'text-danger';
                                    }
                                }

                                return (
                                    <React.Fragment key={tx.id}>
                                        <tr className={`transaction-entry-row border-b border-glass-border hover:bg-white hover:bg-opacity-5 transition-colors${showAdd && editingTxId === tx.id ? ' transaction-entry-row-active' : ''}`}>
                                            <td className="p-4 whitespace-nowrap">
                                                {formatDate(tx.date, dateFormat)}
                                                <div className="text-xs text-muted">ID #{tx.id}</div>
                                            </td>
                                            <td className="p-4">
                                                <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${badgeClass}`}>
                                                    {icon}
                                                    {typeLabel}
                                                </div>
                                            </td>
                                            <td className="p-4">
                                                {tx.category ? (
                                                    <span className="inline-block px-2 py-1 bg-white bg-opacity-5 border border-glass-border rounded text-xs">
                                                        {tx.category}
                                                    </span>
                                                ) : '-'}
                                            </td>
                                            <td className="p-4 text-text-secondary">{tx.description || '-'}</td>
                                            <td className={`p-4 text-right font-medium ${textClass}`}>
                                                {formatMoney(tx.amount, bank.currency, true)}
                                            </td>
                                            <td className="p-4 text-center transaction-actions-cell">
                                                <div className="transaction-actions">
                                                {(tx.type !== 'transfer' || tx.transaction_id !== `entry:${tx.id}`) && <button
                                                    onClick={async () => {
                                                        if (showAdd && editingTxId === tx.id) {
                                                            setShowAdd(false);
                                                            setEditingTxId(null);
                                                            setTransferPair(null);
                                                            return;
                                                        }
                                                        if (tx.type === 'transfer') {
                                                            try {
                                                                const pair = await transactionsApi.getTransfer(tx.transaction_id);
                                                                const other = pair.debit.id === tx.id ? pair.credit : pair.debit;
                                                                setTransferPair(pair);
                                                                setOtherAmount(Math.abs(other.amount).toString());
                                                            } catch (err) {
                                                                console.error('Failed to load transfer pair', err);
                                                                showModal({ title: 'Oops!', message: 'Failed to load both sides of this transfer.', variant: 'danger', alertOnly: true, onConfirm: closeModal });
                                                                return;
                                                            }
                                                        } else {
                                                            setTransferPair(null);
                                                            setOtherAmount('');
                                                        }
                                                        setEditingTxId(tx.id);
                                                        setAmount(Math.abs(tx.amount).toString());
                                                        setType(tx.type);
                                                        setDesc(tx.type === 'transfer' ? transferNote(tx.description) : tx.description || '');
                                                        setTxDate(formatDate(tx.date, dateFormat));
                                                        setIsCreatingCat(false);
                                                        setNewCatName('');
                                                    
                                                        // Resolve category selection
                                                        if (tx.category) {
                                                            const cat = categories.find(c => c.name === tx.category);
                                                            if (cat) {
                                                                setSelectedCatId(cat.id.toString());
                                                            } else {
                                                                setSelectedCatId('CURRENT');
                                                            }
                                                        } else {
                                                            setSelectedCatId('');
                                                        }
                                                    
                                                        setShowAdd(true);
                                                    }}
                                                    className="text-text-secondary hover:text-accent-primary p-1 transition-colors animate-fade-in"
                                                    title="Edit Transaction"
                                                    aria-expanded={showAdd && editingTxId === tx.id}
                                                    aria-controls={`transaction-editor-${tx.id}`}
                                                    style={{ border: 'none', background: 'transparent', cursor: 'pointer', outline: 'none', padding: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                                                >
                                                    <Pencil size={14} />
                                                </button>}
                                                <button
                                                    onClick={() => {
                                                        showModal({
                                                            title: 'Delete Transaction',
                                                            message: tx.type === 'transfer' ? 'Delete both sides of this PiggyBank transfer? This action cannot be undone.' : 'Are you sure you want to delete this transaction? This action cannot be undone.',
                                                            variant: 'danger',
                                                            confirmText: 'Delete',
                                                            onConfirm: async () => {
                                                                closeModal();
                                                                try {
                                                                    await transactionsApi.delete(tx.id);
                                                                    if (editingTxId === tx.id) {
                                                                        setShowAdd(false);
                                                                        setEditingTxId(null);
                                                                    }
                                                                    await loadData({ silent: true });
                                                                } catch (err) {
                                                                    console.error(err);
                                                                    showModal({ title: 'Error', message: 'Failed to delete transaction.', variant: 'danger', alertOnly: true, onConfirm: closeModal });
                                                                }
                                                            },
                                                        });
                                                    }}
                                                    className="text-text-secondary hover:text-danger p-1 transition-colors"
                                                    title="Delete Transaction"
                                                    style={{ border: 'none', background: 'transparent', cursor: 'pointer', outline: 'none', padding: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                                                >
                                                    ✕
                                                </button>
                                                </div>
                                            </td>
                                        </tr>
                                        {showAdd && editingTxId === tx.id && (
                                            <tr className="transaction-edit-row">
                                                <td colSpan={6} className="transaction-edit-cell">
                                                    {transactionForm}
                                                </td>
                                            </tr>
                                        )}
                                    </React.Fragment>
                                );
                            })}
                        </tbody>
                    </table>
                )}
                {totalPages > 1 && (
                    <nav className="transaction-pagination" aria-label="Transaction pages">
                        <span className="text-sm text-muted">
                            {firstShown}–{lastShown} of {matchingTransactions.length}
                        </span>
                        <div className="transaction-pagination-controls">
                            <button
                                type="button"
                                className="btn btn-secondary transaction-page-button"
                                onClick={() => goToPage(currentPage - 1)}
                                disabled={currentPage === 1}
                                aria-label="Previous page"
                            >
                                <ChevronLeft size={16} />
                            </button>
                            {nearbyPages.map(number => (
                                <button
                                    key={number}
                                    type="button"
                                    className={`btn btn-secondary transaction-page-button${number === currentPage ? ' is-current' : ''}`}
                                    onClick={() => goToPage(number)}
                                    aria-current={number === currentPage ? 'page' : undefined}
                                    aria-label={`Page ${number}`}
                                >
                                    {number}
                                </button>
                            ))}
                            {pageWindowEnd < totalPages && (
                                <>
                                    {pageWindowEnd < totalPages - 1 && <span className="transaction-page-ellipsis" aria-hidden="true">…</span>}
                                    <button type="button" className="btn btn-secondary transaction-page-button" onClick={() => goToPage(totalPages)} aria-label={`Page ${totalPages}`}>
                                        {totalPages}
                                    </button>
                                </>
                            )}
                            <button
                                type="button"
                                className="btn btn-secondary transaction-page-button"
                                onClick={() => goToPage(currentPage + 1)}
                                disabled={currentPage === totalPages}
                                aria-label="Next page"
                            >
                                <ChevronRight size={16} />
                            </button>
                        </div>
                        <form className="transaction-page-jump" onSubmit={event => {
                            event.preventDefault();
                            const text = pageInput.trim();
                            const target = Number(text);
                            if (!/^\d+$/.test(text) || !Number.isSafeInteger(target) || target < 1 || target > totalPages) {
                                setPageError(`Enter a whole page number from 1 to ${totalPages}.`);
                                return;
                            }
                            goToPage(target);
                        }}>
                            <label htmlFor="transaction-page-input">Go to page</label>
                            <input
                                id="transaction-page-input"
                                type="text"
                                inputMode="numeric"
                                className="input-field"
                                placeholder={`1–${totalPages}`}
                                value={pageInput}
                                onChange={event => { setPageInput(event.target.value); setPageError(''); }}
                                aria-invalid={!!pageError}
                                aria-describedby={pageError ? 'transaction-page-error' : undefined}
                            />
                            <button type="submit" className="btn btn-secondary">Go</button>
                            {pageError && <span id="transaction-page-error" className="text-sm text-danger" role="alert">{pageError}</span>}
                        </form>
                    </nav>
                )}
            </div>

            {!showAdd && <FloatingTools showAnalytics={showAnalytics} setShowAnalytics={setShowAnalytics} />}

            {settingsOpen && <SettingsDialog onClose={() => setSettingsOpen(false)} opener={settingsButtonRef.current} />}

            <ConfirmModal
                isOpen={modalOpen}
                title={modalConfig.title}
                message={modalConfig.message}
                variant={modalConfig.variant}
                confirmText={modalConfig.confirmText}
                alertOnly={modalConfig.alertOnly}
                onConfirm={modalConfig.onConfirm}
                onCancel={closeModal}
            />
        </div>
    );
};
