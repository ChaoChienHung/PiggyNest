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
import { FilterPicker } from '../components/FilterPicker';
import { formatMoney } from '../utils/money';
import { useAuth } from '../context/useAuth';
import { useRates } from '../context/useRates';
import { convertAmount } from '../utils/currency';
import { asDateFormat, formatDate, formatMonth, formatPeriod, isoDatePart, parseDate, todayIsoDate } from '../utils/dates';
import { periodKey } from '../utils/ledgerAnalytics';

const transferNote = (description?: string) => {
    const note = description || '';
    const separator = note.indexOf(': ');
    return separator >= 0 ? note.slice(separator + 2) : note;
};

const TYPE_ORDER = ['expense', 'income', 'transfer', 'transfer_out', 'transfer_in', 'deposit', 'withdrawal'];
const transactionTypeLabel = (txType: string) => {
    switch (txType) {
        case 'expense': return 'Expense';
        case 'income': return 'Income';
        case 'transfer': return 'PiggyBank Transfer';
        case 'transfer_out': return 'Bank Transfer Out';
        case 'transfer_in': return 'Bank Transfer In';
        case 'deposit': return 'Deposit';
        case 'withdrawal': return 'Withdrawal';
        default: return txType;
    }
};

/**
 * Dedicated view for a single PiggyBank account.
 * Handles fetching specific nested transactions and managing the dynamic "Add Transaction" form logic.
 */
export const PiggyBankView = ({ analyticsOnly = false, bankId }: { analyticsOnly?: boolean; bankId?: number }) => {
    const { id: routeId } = useParams<{ id: string }>();
    const id = bankId ? String(bankId) : routeId;
    const [bank, setBank] = useState<PiggyBank | null>(null);
    const [balance, setBalance] = useState<Balance | null>(null);
    const [transactions, setTransactions] = useState<Transaction[]>([]);

    // For transfer form
    const [allBanks, setAllBanks] = useState<PiggyBank[]>([]);
    const [categories, setCategories] = useState<Category[]>([]);

    const [isLoading, setIsLoading] = useState(true);
    const [settingsOpen, setSettingsOpen] = useState(false);
    const settingsButtonRef = React.useRef<HTMLButtonElement>(null);
    const [lineMetric, setLineMetric] = useState<'balance' | 'income' | 'expense'>('balance');
    const [viewScale, setViewScale] = useState<'day' | 'month' | 'year'>('day');

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
    const [categoryFilters, setCategoryFilters] = useState<string[] | null>(null);
    const [typeFilters, setTypeFilters] = useState<string[] | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectionMode, setSelectionMode] = useState(false);
    const [selectedTxIds, setSelectedTxIds] = useState<number[]>([]);
    const [bulkCategory, setBulkCategory] = useState('');
    const [bulkBusy, setBulkBusy] = useState(false);
    const [analysisCategories, setAnalysisCategories] = useState<string[] | null>(null);
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
    const filterCategories = [...new Set(transactions.map(tx => tx.category || ''))].sort((a, b) => a.localeCompare(b));
    const selectedFilterCategories = categoryFilters ?? filterCategories;
    const filterTypes = [...new Set(transactions.map(tx => tx.type))].sort((a, b) => {
        const idxA = TYPE_ORDER.indexOf(a);
        const idxB = TYPE_ORDER.indexOf(b);
        return (idxA === -1 ? 99 : idxA) - (idxB === -1 ? 99 : idxB) || a.localeCompare(b);
    });
    const selectedFilterTypes = typeFilters ?? filterTypes;
    const normalizedSearch = searchQuery.trim().toLowerCase();
    const matchesSearch = (tx: Transaction) => {
        if (!normalizedSearch) return true;
        const fields = [
            tx.description || '',
            tx.category || '',
            `#${tx.id}`,
            String(tx.id),
            String(tx.amount),
            Math.abs(tx.amount).toFixed(2),
            formatMoney(tx.amount, bank.currency, true),
        ];
        return fields.some(value => value.toLowerCase().includes(normalizedSearch));
    };
    const matchingTransactions = transactions.filter(tx =>
        inDateRange(tx)
        && selectedFilterCategories.includes(tx.category || '')
        && selectedFilterTypes.includes(tx.type)
        && matchesSearch(tx)
    ).sort((a, b) => {
        const result = sortField === 'date'
            ? isoDatePart(a.date).localeCompare(isoDatePart(b.date))
            : a.amount - b.amount;
        return (sortDirection === 'asc' ? result : -result) || b.id - a.id;
    });
    const matchingIdSet = new Set(matchingTransactions.map(tx => tx.id));
    const activeSelectedIds = selectedTxIds.filter(txId => matchingIdSet.has(txId));
    const activeSelectedSet = new Set(activeSelectedIds);
    const selectedTransactions = matchingTransactions.filter(tx => activeSelectedSet.has(tx.id));
    const selectedTransferCount = selectedTransactions.filter(tx => tx.type === 'transfer').length;
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
    const visibleIds = visibleTransactions.map(tx => tx.id);
    const allVisibleSelected = visibleIds.length > 0 && visibleIds.every(txId => activeSelectedSet.has(txId));
    const toggleRowSelection = (txId: number) => {
        setSelectedTxIds(prev => {
            const valid = prev.filter(item => matchingIdSet.has(item));
            return valid.includes(txId) ? valid.filter(item => item !== txId) : [...valid, txId];
        });
    };
    const toggleVisibleSelection = () => {
        setSelectedTxIds(prev => {
            const valid = prev.filter(item => matchingIdSet.has(item));
            if (allVisibleSelected) {
                return valid.filter(item => !visibleIds.includes(item));
            }
            const next = new Set(valid);
            visibleIds.forEach(txId => next.add(txId));
            return [...next];
        });
    };
    const handleBulkApplyCategory = async () => {
        if (!activeSelectedIds.length || selectedTransferCount > 0 || !bulkCategory) return;
        const targetCategory = bulkCategory === '__CLEAR__' ? null : bulkCategory;
        setBulkBusy(true);
        try {
            await transactionsApi.bulkUpdateCategory(activeSelectedIds, targetCategory);
            setSelectedTxIds([]);
            setBulkCategory('');
            setSelectionMode(false);
            await loadData({ silent: true });
        } catch (err) {
            console.error('Bulk category update failed', err);
            showModal({
                title: 'Bulk Update Failed',
                message: 'Could not update categories for the selected transactions.',
                variant: 'danger',
                alertOnly: true,
                onConfirm: closeModal,
            });
        } finally {
            setBulkBusy(false);
        }
    };
    const handleBulkDelete = () => {
        if (!activeSelectedIds.length) return;
        const transferWarning = selectedTransferCount > 0
            ? ` Includes ${selectedTransferCount} PiggyBank transfer${selectedTransferCount > 1 ? 's' : ''} — both sides of each PiggyBank transfer will be removed.`
            : '';
        showModal({
            title: 'Delete Selected Transactions',
            message: `Delete ${activeSelectedIds.length} selected transaction${activeSelectedIds.length > 1 ? 's' : ''}?${transferWarning} This action cannot be undone.`,
            variant: 'danger',
            confirmText: 'Delete',
            onConfirm: async () => {
                closeModal();
                setBulkBusy(true);
                try {
                    await transactionsApi.bulkDelete(activeSelectedIds);
                    if (editingTxId !== null && activeSelectedSet.has(editingTxId)) {
                        setShowAdd(false);
                        setEditingTxId(null);
                    }
                    setSelectedTxIds([]);
                    setBulkCategory('');
                    setSelectionMode(false);
                    await loadData({ silent: true });
                } catch (err) {
                    console.error('Bulk delete failed', err);
                    showModal({
                        title: 'Bulk Delete Failed',
                        message: 'Could not delete the selected transactions.',
                        variant: 'danger',
                        alertOnly: true,
                        onConfirm: closeModal,
                    });
                } finally {
                    setBulkBusy(false);
                }
            },
        });
    };
    const firstShown = matchingTransactions.length === 0 ? 0 : (currentPage - 1) * (pageSize || matchingTransactions.length) + 1;
    const lastShown = firstShown + visibleTransactions.length - 1;
    const analyticsTransactions = transactions.filter(tx => inDateRange(tx) &&
        (analysisCategories === null || analysisCategories.includes(tx.category || '')));

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

    // Group transactions by the selected view scale (daily, monthly, or yearly).
    // On daily scale, `t` is UTC midnight so the time axis spaces calendar days evenly.
    const periodTotals = new Map<string, { income: number; expense: number; net: number }>();
    for (const tx of analyticsTransactions) {
        const key = periodKey(isoDatePart(tx.date), viewScale);
        const totals = periodTotals.get(key) ?? { income: 0, expense: 0, net: 0 };
        if (tx.type !== 'transfer') {
            if (tx.amount > 0) totals.income += tx.amount;
            else totals.expense += Math.abs(tx.amount);
        }
        totals.net += tx.amount;
        periodTotals.set(key, totals);
    }
    let runningBalance = appliedFrom
        ? transactions.filter(tx => isoDatePart(tx.date) < appliedFrom).reduce((sum, tx) => sum + tx.amount, 0)
        : 0;
    const lineChartData = [...periodTotals.entries()]
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([period, totals]) => {
            runningBalance += totals.net;
            const [y, m = 1, d = 1] = period.split('-').map(Number);
            return {
                t: Date.UTC(y, m - 1, d),
                period,
                balance: Math.round(runningBalance * 100) / 100,
                income: Math.round(totals.income * 100) / 100,
                expense: Math.round(totals.expense * 100) / 100,
            };
        });

    // Tick at the start of each month in range on daily scale, thinned to at most ~8 labels.
    const monthTicks: number[] = [];
    if (viewScale === 'day' && lineChartData.length > 0) {
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
            ? formatMonth(`${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, '0')}`, dateFormat)
            : formatDate(date.toISOString(), dateFormat);
    };
    const lineColor = lineMetric === 'expense' ? '#ff8da1' : '#f4b740';
    const scaleLabel = viewScale === 'day' ? 'Daily' : viewScale === 'month' ? 'Monthly' : 'Yearly';
    const barData = lineChartData;

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
                            ...(editingTxId !== null && type === 'withdrawal' ? [{ value: 'withdrawal', label: 'Withdrawal' }] : []),
                            ...(editingTxId !== null && type === 'deposit' ? [{ value: 'deposit', label: 'Deposit' }] : []),
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

    const analyticsPanel = (
                <div className="glass-panel p-6 mb-8 animate-fade-in">
                    <div className="analytics-heading mb-6">
                        <h3 className="text-xl font-bold">PiggyBank Analytics</h3>
                        <div className="analytics-heading-actions">
                            <ThemedSelect
                                ariaLabel="View scale"
                                className="analytics-select"
                                value={viewScale}
                                onChange={(value) => setViewScale(value as 'day' | 'month' | 'year')}
                                options={[
                                    { value: 'day', label: 'Daily' },
                                    { value: 'month', label: 'Monthly' },
                                    { value: 'year', label: 'Yearly' },
                                ]}
                            />
                            <ThemedSelect
                                ariaLabel="Analytics metric"
                                className="analytics-select"
                                value={lineMetric}
                                onChange={(value) => setLineMetric(value as 'balance' | 'income' | 'expense')}
                                options={[
                                    { value: 'balance', label: 'Running Balance' },
                                    { value: 'income', label: 'Income' },
                                    { value: 'expense', label: 'Expenses' },
                                ]}
                            />

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
                                    {viewScale === 'day' ? (
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
                                    ) : (
                                        <XAxis
                                            dataKey="period"
                                            tickFormatter={value => formatPeriod(String(value), viewScale, dateFormat)}
                                            minTickGap={24}
                                            stroke="#8c768f"
                                            style={{ fontSize: '0.85rem', fontWeight: 600 }}
                                        />
                                    )}
                                    <YAxis stroke="#8c768f" style={{ fontSize: '0.85rem', fontWeight: 600 }} width={56} />
                                    <Tooltip
                                        labelFormatter={(value) => viewScale === 'day'
                                            ? formatDate(new Date(Number(value)).toISOString(), dateFormat)
                                            : formatPeriod(String(value), viewScale, dateFormat)}
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
                                        type="monotone"
                                        dataKey={lineMetric}
                                        name={
                                            lineMetric === 'balance' ? 'Running Balance' :
                                            lineMetric === 'income' ? 'Income' :
                                            'Expenses'
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
                            {/* Bar Chart: Period Summary */}
                            <div>
                                <h4 className="text-center font-semibold mb-4 text-text-secondary">{scaleLabel} Summary</h4>
                                <div style={{ height: '250px', width: '100%' }}>
                                    {barData.length > 0 ? (
                                        <ResponsiveContainer width="100%" height="100%">
                                            <BarChart
                                                data={barData}
                                                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                                            >
                                                <CartesianGrid strokeDasharray="4 4" stroke="rgba(255, 141, 161, 0.15)" />
                                                <XAxis
                                                    dataKey="period"
                                                    minTickGap={24}
                                                    tickFormatter={value => formatPeriod(String(value), viewScale, dateFormat)}
                                                    stroke="#8c768f"
                                                    style={{ fontSize: '0.8rem', fontWeight: 600 }}
                                                />
                                                <YAxis stroke="#8c768f" style={{ fontSize: '0.8rem', fontWeight: 600 }} />
                                                <Tooltip
                                                    labelFormatter={value => formatPeriod(String(value), viewScale, dateFormat)}
                                                    formatter={(value) => formatMoney(Number(value), bank.currency)}
                                                    cursor={{ fill: 'rgba(255, 141, 161, 0.05)' }}
                                                    contentStyle={{ 
                                                        backgroundColor: 'rgba(255, 255, 255, 0.95)', 
                                                        border: '2px solid rgba(255, 141, 161, 0.2)', 
                                                        borderRadius: '16px',
                                                        color: '#4a3e4b'
                                                    }}
                                                />
                                                <Legend />
                                                <Bar dataKey="income" name="Income" fill="#ffd166" radius={[6, 6, 0, 0]} maxBarSize={35} />
                                                <Bar dataKey="expense" name="Expenses" fill="#ff8da1" radius={[6, 6, 0, 0]} maxBarSize={35} />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    ) : (
                                        <div className="flex h-full items-center justify-center text-muted text-sm pb-8">No {scaleLabel.toLowerCase()} flow data yet.</div>
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


    );
    if (analyticsOnly) return <main className="container page-layout-container with-floating-tools animate-fade-in analysis-page">
        <Link to={`/piggybanks/${bank.id}`} className="back-to-dashboard-link">← Back to {bank.name}</Link>
        <h1 className="dashboard-title">Graph Analysis</h1>
        <div className="glass-panel p-6 mb-8">
            <div className="analytics-picker-row">
                <FilterPicker label="Categories" options={filterCategories.map(category => ({ value: category, label: category || 'Uncategorized' }))}
                    selected={analysisCategories ?? filterCategories} onChange={setAnalysisCategories}
                    emptyLabel="None" allLabel="All categories" clearLabel="Clear" />
            </div>
            <div className="analytics-date-filter">
                <DateTextField id="analysis-date-from" label={`From (${dateFormat})`} value={dateFromText}
                    onChange={value => changeDateRange(value, dateToText)} dateFormat={dateFormat} invalid={!!dateRangeError} />
                <DateTextField id="analysis-date-to" label={`To (${dateFormat})`} value={dateToText}
                    onChange={value => changeDateRange(dateFromText, value)} dateFormat={dateFormat} invalid={!!dateRangeError} />
                {dateRangeError && <span className="text-sm text-danger" role="alert">{dateRangeError}</span>}
            </div>
        </div>
        {analyticsPanel}
        <FloatingTools bankId={bank.id} />
    </main>;

    return (
        <div className="container page-layout-container animate-fade-in with-floating-tools">
            <div className="piggybank-page-header">
                <Link to="/" className="back-to-dashboard-link">
                    <ArrowLeft size={16} className="mr-2" /> Back to Dashboard
                </Link>
                <div className="piggybank-header-actions">
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
                    {transactions.length > 0 && (
                        <button
                            type="button"
                            className="btn btn-secondary"
                            aria-pressed={selectionMode}
                            onClick={() => {
                                setSelectionMode(prev => {
                                    if (prev) {
                                        setSelectedTxIds([]);
                                        setBulkCategory('');
                                    }
                                    return !prev;
                                });
                            }}
                        >
                            {selectionMode ? 'Done' : 'Select'}
                        </button>
                    )}
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
                    <FilterPicker label="Types" options={filterTypes.map(txType => ({ value: txType, label: transactionTypeLabel(txType) }))}
                        selected={selectedFilterTypes} onChange={values => { setTypeFilters(values); setPage(1); }}
                        emptyLabel="None" allLabel="Select all" clearLabel="Clear" />
                    <FilterPicker label="Categories" options={filterCategories.map(category => ({ value: category, label: category || 'Uncategorized' }))}
                        selected={selectedFilterCategories} onChange={values => { setCategoryFilters(values); setPage(1); }}
                        emptyLabel="None" allLabel="Select all" clearLabel="Clear" />
                    <div>
                        <label htmlFor="filter-search" className="text-sm font-medium text-text-secondary">Search</label>
                        <input
                            id="filter-search"
                            type="search"
                            className="input-field"
                            placeholder="Description, #ID, amount..."
                            value={searchQuery}
                            onChange={event => { setSearchQuery(event.target.value); setPage(1); }}
                        />
                    </div>
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
                        setCategoryFilters(null);
                        setTypeFilters(null);
                        setSearchQuery('');
                        setSelectedTxIds([]);
                        setDateFromText('');
                        setDateToText('');
                        setAppliedFrom(null);
                        setAppliedTo(null);
                        setPage(1);
                    }}>Clear filters</button>
                </div>
            </div>

            <div className="glass-panel transaction-table-panel">
                {selectionMode && activeSelectedIds.length > 0 && (
                    <div className="bulk-action-bar" role="region" aria-label="Bulk transaction actions">
                        <div className="bulk-action-summary">
                            <span className="text-sm font-semibold">{activeSelectedIds.length} selected</span>
                            {activeSelectedIds.length < matchingTransactions.length && (
                                <button
                                    type="button"
                                    className="btn btn-secondary text-xs"
                                    onClick={() => setSelectedTxIds(matchingTransactions.map(tx => tx.id))}
                                >
                                    Select all {matchingTransactions.length} matching
                                </button>
                            )}
                            <button
                                type="button"
                                className="btn btn-secondary text-xs"
                                onClick={() => setSelectedTxIds([])}
                            >
                                Clear selection
                            </button>
                        </div>
                        <div className="bulk-action-controls">
                            {selectedTransferCount > 0 ? (
                                <span className="text-xs text-muted">PiggyBank transfer categories cannot be changed.</span>
                            ) : (
                                <>
                                    <div className="bulk-category-select">
                                        <ThemedSelect
                                            id="bulk-category-select"
                                            value={bulkCategory}
                                            onChange={setBulkCategory}
                                            options={[
                                                { value: '', label: 'Set category...' },
                                                ...categories.map(cat => ({ value: cat.name, label: cat.name })),
                                                { value: '__CLEAR__', label: 'Uncategorized' },
                                            ]}
                                        />
                                    </div>
                                    <button
                                        type="button"
                                        className="btn btn-primary text-sm"
                                        disabled={!bulkCategory || bulkBusy}
                                        onClick={handleBulkApplyCategory}
                                    >
                                        Apply
                                    </button>
                                </>
                            )}
                            <button
                                type="button"
                                className="btn btn-danger text-sm"
                                disabled={bulkBusy}
                                onClick={handleBulkDelete}
                            >
                                Delete Selected
                            </button>
                        </div>
                    </div>
                )}
                {matchingTransactions.length === 0 ? (
                    <div className="p-8 text-center text-muted">{transactions.length ? 'No transactions match these filters.' : 'No transactions found.'}</div>
                ) : (
                    <table className={`w-full text-left border-collapse transaction-table${selectionMode ? ' is-selecting' : ''}`}>
                        <thead>
                            <tr className="border-b border-glass-border">
                                {selectionMode && (
                                    <th className="p-4 text-center" style={{ width: '44px' }}>
                                        <input
                                            type="checkbox"
                                            className="tx-select-checkbox"
                                            checked={allVisibleSelected}
                                            onChange={toggleVisibleSelection}
                                            aria-label="Select all transactions on this page"
                                        />
                                    </th>
                                )}
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
                                        <tr className={`transaction-entry-row border-b border-glass-border hover:bg-white hover:bg-opacity-5 transition-colors${showAdd && editingTxId === tx.id ? ' transaction-entry-row-active' : ''}${selectionMode && activeSelectedSet.has(tx.id) ? ' transaction-entry-row-selected' : ''}`}>
                                            {selectionMode && (
                                                <td className="p-4 text-center">
                                                    <input
                                                        type="checkbox"
                                                        className="tx-select-checkbox"
                                                        checked={activeSelectedSet.has(tx.id)}
                                                        onChange={() => toggleRowSelection(tx.id)}
                                                        aria-label={`Select transaction #${tx.id}`}
                                                    />
                                                </td>
                                            )}
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
                                                <td colSpan={selectionMode ? 7 : 6} className="transaction-edit-cell">
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

            <FloatingTools bankId={bank.id} />

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
