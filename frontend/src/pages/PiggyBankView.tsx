import React, { useEffect, useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { piggybanksApi } from '../api/piggybanks';
import { transactionsApi } from '../api/transactions';
import { categoriesApi } from '../api/categories';
import type { Transaction, PiggyBank, Balance, Category } from '../types';
import { ArrowLeft, ArrowUpRight, ArrowDownRight, ArrowRight, Plus, Pencil, TrendingUp } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { ConfirmModal, type ModalVariant } from '../components/ConfirmModal';

const CATEGORY_COLORS = ['#ff8da1', '#ffd166', '#ffb703', '#ff5e7e', '#ffc2d1', '#f59e0b', '#ec4899', '#8b5cf6'];

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
    const [lineMetric, setLineMetric] = useState<'balance' | 'income' | 'expense'>('balance');

    // Form states
    const [showAdd, setShowAdd] = useState(false);
    const [editingTxId, setEditingTxId] = useState<number | null>(null);
    const [amount, setAmount] = useState('');
    const [type, setType] = useState('expense');
    const [desc, setDesc] = useState('');
    const [txDate, setTxDate] = useState(new Date().toISOString().split('T')[0]);

    // Category states
    const [selectedCatId, setSelectedCatId] = useState('');
    const [newCatName, setNewCatName] = useState('');
    const [isCreatingCat, setIsCreatingCat] = useState(false);

    // Transfer states
    const [targetBankId, setTargetBankId] = useState('');

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

    /**
     * Re-fetches all critical data relating to this specific PiggyBank.
     * Grabs underlying transactions, current balance totals, and external categories/PiggyBanks for dropdowns.
     */
    const loadData = useCallback(async () => {
        if (!id) return;
        setIsLoading(true);
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

        try {
            // First resolve category
            let finalCategoryName = '';
            if (type !== 'transfer' && isCreatingCat && newCatName.trim() !== '') {
                const newCat = await categoriesApi.create(newCatName.trim());
                finalCategoryName = newCat.name;
            } else if (selectedCatId) {
                const cat = categories.find(c => c.id.toString() === selectedCatId);
                if (cat) finalCategoryName = cat.name;
            }

            if (editingTxId !== null) {
                let finalDate = undefined;
                if (txDate) {
                    finalDate = new Date(txDate).toISOString();
                }
                await transactionsApi.update(editingTxId, finalAmount, type, desc, finalCategoryName, finalDate);
            } else if (type === 'transfer') {
                if (!targetBankId) {
                    showModal({ title: 'Missing Target', message: 'Please select a target Piggy Bank for transfer.', variant: 'warning', alertOnly: true, onConfirm: closeModal });
                    return;
                }
                const amt = Math.abs(parseFloat(amount));
                await transactionsApi.transfer(parseInt(id), parseInt(targetBankId), amt, desc);
            } else {
                let finalDate = undefined;
                if (txDate) {
                    finalDate = new Date(txDate).toISOString();
                }
                await transactionsApi.create(parseInt(id), finalAmount, type, desc, finalCategoryName, finalDate);
            }

            setShowAdd(false);
            setAmount('');
            setDesc('');
            setSelectedCatId('');
            setNewCatName('');
            setIsCreatingCat(false);
            setType('expense');
            setTxDate(new Date().toISOString().split('T')[0]);
            setEditingTxId(null);
            loadData();
        } catch (err) {
            console.error("Failed to save transaction", err);
            showModal({ title: 'Oops!', message: 'Failed to save transaction. Please try again.', variant: 'danger', alertOnly: true, onConfirm: closeModal });
        }
    };

    if (isLoading) return <div className="p-8 text-center text-muted animate-fade-in">Loading...</div>;
    if (!bank) return <div className="p-8 text-center text-danger animate-fade-in">PiggyBank not found.</div>;

    const transferTargets = allBanks.filter(b => b.id !== bank.id && b.currency === bank.currency);

    const getCurrencySymbol = (currency: string) => {
        switch (currency) {
            case 'USD': return '$';
            case 'EUR': return '€';
            case 'GBP': return '£';
            case 'JPY': return '¥';
            case 'NTD': return 'NT$';
            case 'SGD': return 'S$';
            default: return currency + ' ';
        }
    };
    // Sort transactions chronologically ascending to compute running balance
    const chronologicalTxs = [...transactions].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    
    let runningBalance = 0;
    const lineChartData = chronologicalTxs.map(tx => {
        runningBalance += tx.amount;
        const dateStr = new Date(tx.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
        return {
            rawDate: new Date(tx.date),
            dateStr,
            balance: parseFloat(runningBalance.toFixed(2)),
            income: tx.amount > 0 ? tx.amount : 0,
            expense: tx.amount < 0 ? Math.abs(tx.amount) : 0
        };
    });

    // Group monthly for Bar Chart
    const monthlyTotals: Record<string, { month: string, income: number, expense: number }> = {};
    transactions.forEach(tx => {
        const date = new Date(tx.date);
        const monthStr = date.toLocaleDateString(undefined, { year: 'numeric', month: 'short' });
        if (!monthlyTotals[monthStr]) {
            monthlyTotals[monthStr] = { month: monthStr, income: 0, expense: 0 };
        }
        if (tx.amount > 0) {
            monthlyTotals[monthStr].income += tx.amount;
        } else {
            monthlyTotals[monthStr].expense += Math.abs(tx.amount);
        }
    });
    const barData = Object.values(monthlyTotals).reverse();

    // Group category totals for Pie Chart
    const catTotals: Record<string, number> = {};
    transactions.forEach(tx => {
        if (tx.amount < 0 && tx.category) {
            catTotals[tx.category] = (catTotals[tx.category] || 0) + Math.abs(tx.amount);
        }
    });
    const pieData = Object.entries(catTotals)
        .map(([name, value]) => ({ name, value }))
        .filter(d => d.value > 0)
        .sort((a, b) => b.value - a.value);

    const cSym = getCurrencySymbol(bank.currency);

    return (
        <div className="container page-layout-container animate-fade-in">
            <Link to="/" className="back-to-dashboard-link">
                <ArrowLeft size={16} className="mr-2" /> Back to Dashboard
            </Link>

            <div className="glass-panel balance-card mb-8">
                <div className="balance-card-header">
                    <h1 className="balance-card-title">{bank.name} 🐷</h1>
                    <p className="balance-card-subtitle">PiggyBank Details & Savings Nest 💰</p>
                </div>
                
                <div className="balance-card-divider" />
                
                <div className="balance-card-body">
                    <p className="balance-card-label">Current Balance</p>
                    <h2 className="balance-card-amount">
                        {cSym}{balance?.balance.toFixed(2) || '0.00'}
                    </h2>
                </div>
            </div>

            <div className="flex justify-between items-center mb-6">
                <h2 className="transactions-section-title">Transactions 📜</h2>
                <div className="flex items-center gap-3">
                    {/* Inline Pig Trigger next to Add Transaction */}
                    <div className="inline-fab-container">
                        {/* Option: Toggle Analytics (Gold Coin with Chart Icon) */}
                        <div className="inline-fab-options">
                            <div 
                                onClick={() => setShowAnalytics(!showAnalytics)} 
                                className="inline-fab-coin"
                                title={showAnalytics ? "Hide Charts" : "Show Charts"}
                            >
                                <TrendingUp size={20} />
                                <span className="inline-fab-tooltip">
                                    {showAnalytics ? "📊 Hide Analytics" : "📈 Show Analytics"}
                                </span>
                            </div>
                        </div>
                        {/* Main Trigger (Circle with Piggy inside) */}
                        <div className="inline-fab-trigger" title="Piggy Options">
                            🐷
                        </div>
                    </div>

                    <button
                        onClick={() => {
                            if (showAdd && editingTxId !== null) {
                                setAmount('');
                                setDesc('');
                                setSelectedCatId('');
                                setNewCatName('');
                                setIsCreatingCat(false);
                                setType('expense');
                                setTxDate(new Date().toISOString().split('T')[0]);
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

            {showAdd && (
                <form onSubmit={handleAddTx} className="glass-panel p-6 mb-8 animate-fade-in flex flex-col gap-4">
                    <h3 className="text-lg font-semibold mb-2">{editingTxId ? 'Edit Transaction ✏️' : 'Add New Transaction 📝'}</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">Type</label>
                            <select
                                className="input-field"
                                value={type}
                                onChange={(e) => setType(e.target.value)}
                            >
                                <option value="expense">Expense</option>
                                <option value="income">Income</option>
                                <option value="withdrawal">Withdrawal</option>
                                <option value="deposit">Deposit</option>
                                <option value="transfer_out">Transfer Out (external)</option>
                                <option value="transfer_in">Transfer In (external)</option>
                                {editingTxId === null && <option value="transfer">Transfer between PiggyBanks</option>}
                            </select>
                        </div>

                        {type !== 'transfer' && (
                            <div>
                                <label className="block text-sm font-medium text-text-secondary mb-1">Date</label>
                                <input
                                    type="date"
                                    required
                                    className="input-field"
                                    value={txDate}
                                    onChange={(e) => setTxDate(e.target.value)}
                                />
                            </div>
                        )}

                        {type === 'transfer' && (
                            <div>
                                <label className="block text-sm font-medium text-text-secondary mb-1">Transfer To</label>
                                <select
                                    required
                                    className="input-field"
                                    value={targetBankId}
                                    onChange={(e) => setTargetBankId(e.target.value)}
                                >
                                    <option value="">Select Piggy Bank...</option>
                                    {transferTargets.map(t => (
                                        <option key={t.id} value={t.id}>{t.name}</option>
                                    ))}
                                </select>
                            </div>
                        )}

                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">Amount</label>
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

                        {type !== 'transfer' && (
                            <div>
                                <label className="block text-sm font-medium text-text-secondary mb-1">Category</label>
                                {isCreatingCat ? (
                                    <div className="flex gap-2">
                                        <input
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
                                    <select
                                        className="input-field"
                                        value={selectedCatId}
                                        onChange={(e) => {
                                            if (e.target.value === 'NEW') setIsCreatingCat(true);
                                            else setSelectedCatId(e.target.value);
                                        }}
                                    >
                                        <option value="">No Category</option>
                                        {categories.map(c => (
                                            <option key={c.id} value={c.id}>{c.name}</option>
                                        ))}
                                        <option value="NEW" className="font-bold text-accent-primary">+ Create New Category</option>
                                    </select>
                                )}
                            </div>
                        )}

                        <div className={type === 'transfer' ? "md:col-span-2" : ""}>
                            <label className="block text-sm font-medium text-text-secondary mb-1">Description</label>
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
                                setDesc('');
                                setSelectedCatId('');
                                setNewCatName('');
                                setIsCreatingCat(false);
                                setType('expense');
                                setTxDate(new Date().toISOString().split('T')[0]);
                                setEditingTxId(null);
                            }} 
                            className="btn btn-secondary text-sm"
                        >
                            Cancel
                        </button>
                        <button type="submit" className="btn btn-primary text-sm">
                            {editingTxId ? 'Save Changes ✏️' : 'Save Transaction 📝'}
                        </button>
                    </div>
                </form>
            )}

            {showAnalytics && (
                <div className="glass-panel p-6 mb-8 animate-fade-in">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-xl font-bold">PiggyBank Analytics 📈</h3>
                        <div className="flex gap-4 items-center">
                            <select
                                className="input-field py-1 px-3 text-sm h-auto"
                                style={{ width: 'auto', display: 'inline-block' }}
                                value={lineMetric}
                                onChange={(e) => setLineMetric(e.target.value as 'balance' | 'income' | 'expense')}
                            >
                                <option value="balance">Running Balance 💰</option>
                                <option value="income">Income / Deposits 💵</option>
                                <option value="expense">Expenses / Withdrawals 💸</option>
                            </select>

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
                                <LineChart
                                    data={lineChartData}
                                    margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                                >
                                    <CartesianGrid strokeDasharray="4 4" stroke="rgba(255, 141, 161, 0.15)" />
                                    <XAxis dataKey="dateStr" stroke="#8c768f" style={{ fontSize: '0.85rem', fontWeight: 600 }} />
                                    <YAxis stroke="#8c768f" style={{ fontSize: '0.85rem', fontWeight: 600 }} />
                                    <Tooltip
                                        contentStyle={{ 
                                            backgroundColor: 'rgba(255, 255, 255, 0.95)', 
                                            border: '2px solid rgba(255, 141, 161, 0.2)', 
                                            borderRadius: '16px',
                                            boxShadow: '0 8px 24px rgba(255, 141, 161, 0.1)',
                                            color: '#4a3e4b'
                                        }}
                                    />
                                    <Legend wrapperStyle={{ paddingTop: '10px' }} />
                                    <Line
                                        type="monotone"
                                        dataKey={lineMetric}
                                        name={
                                            lineMetric === 'balance' ? 'Running Balance' :
                                            lineMetric === 'income' ? 'Income / Deposits' :
                                            'Expenses / Withdrawals'
                                        }
                                        stroke={lineMetric === 'balance' ? '#ffd166' : lineMetric === 'income' ? '#ffd166' : '#ff8da1'}
                                        strokeWidth={3}
                                        dot={{ r: 4, strokeWidth: 1 }}
                                        activeDot={{ r: 8 }}
                                    />
                                </LineChart>
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
                                <h4 className="text-center font-semibold mb-4 text-text-secondary">Expense Categories</h4>
                                <div style={{ height: '250px', width: '100%' }}>
                                    {pieData.length > 0 ? (
                                        <ResponsiveContainer width="100%" height="100%">
                                            <PieChart>
                                                <Pie
                                                    data={pieData}
                                                    cx="50%"
                                                    cy="50%"
                                                    labelLine={false}
                                                    outerRadius={80}
                                                    fill="#8884d8"
                                                    dataKey="value"
                                                >
                                                    {pieData.map((_, index) => (
                                                        <Cell key={`cell-${index}`} fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]} />
                                                    ))}
                                                </Pie>
                                                <Tooltip
                                                    contentStyle={{ 
                                                        backgroundColor: 'rgba(255, 255, 255, 0.95)', 
                                                        border: '2px solid rgba(255, 141, 161, 0.2)', 
                                                        borderRadius: '16px',
                                                        color: '#4a3e4b' 
                                                    }}
                                                />
                                                <Legend />
                                            </PieChart>
                                        </ResponsiveContainer>
                                    ) : (
                                        <div className="flex h-full items-center justify-center text-muted text-sm pb-8">No categorized expenses.</div>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}

            <div className="glass-panel overflow-hidden">
                {transactions.length === 0 ? (
                    <div className="p-8 text-center text-muted">No transactions found.</div>
                ) : (
                    <table className="w-full text-left border-collapse">
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
                            {transactions.map((tx) => {
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
                                    typeLabel = tx.type === 'transfer_out' ? 'Transfer Out' : tx.type === 'transfer_in' ? 'Transfer In' : 'Transfer';
                                    badgeClass = 'bg-accent-light text-accent-primary';
                                    if (tx.amount > 0) {
                                        textClass = 'text-success';
                                    } else {
                                        textClass = 'text-danger';
                                    }
                                }

                                return (
                                    <tr key={tx.id} className="border-b border-glass-border hover:bg-white hover:bg-opacity-5 transition-colors">
                                        <td className="p-4 whitespace-nowrap">
                                            {new Date(tx.date).toLocaleDateString()}
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
                                            {tx.amount > 0 ? '+' : ''}{cSym}{tx.amount.toFixed(2)}
                                        </td>
                                        <td className="p-4 text-center" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', border: 'none' }}>
                                            {tx.type !== 'transfer' && <button
                                                onClick={() => {
                                                    setEditingTxId(tx.id);
                                                    setAmount(Math.abs(tx.amount).toString());
                                                    setType(tx.type);
                                                    setDesc(tx.description || '');
                                                    setTxDate(new Date(tx.date).toISOString().split('T')[0]);
                                                    
                                                    // Resolve category selection
                                                    if (tx.category) {
                                                        const cat = categories.find(c => c.name === tx.category);
                                                        if (cat) {
                                                            setSelectedCatId(cat.id.toString());
                                                        } else {
                                                            setSelectedCatId('');
                                                        }
                                                    } else {
                                                        setSelectedCatId('');
                                                    }
                                                    
                                                    setShowAdd(true);
                                                }}
                                                className="text-text-secondary hover:text-accent-primary p-1 transition-colors animate-fade-in"
                                                title="Edit Transaction"
                                                style={{ border: 'none', background: 'transparent', cursor: 'pointer', outline: 'none', padding: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                                            >
                                                <Pencil size={14} />
                                            </button>}
                                            <button
                                                onClick={() => {
                                                    showModal({
                                                        title: 'Delete Transaction',
                                                        message: tx.type === 'transfer' ? 'Delete both sides of this transfer? This action cannot be undone.' : 'Are you sure you want to delete this transaction? This action cannot be undone.',
                                                        variant: 'danger',
                                                        confirmText: 'Delete',
                                                        onConfirm: async () => {
                                                            closeModal();
                                                            try {
                                                                await transactionsApi.delete(tx.id);
                                                                loadData();
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
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                )}
            </div>

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
