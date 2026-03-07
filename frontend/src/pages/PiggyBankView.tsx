import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { piggybanksApi } from '../api/piggybanks';
import { transactionsApi } from '../api/transactions';
import { categoriesApi } from '../api/categories';
import type { Transaction, PiggyBank, Balance, Category } from '../types';
import { ArrowLeft, ArrowUpRight, ArrowDownRight, ArrowRight, Plus } from 'lucide-react';

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

    // Form states
    const [showAdd, setShowAdd] = useState(false);
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

    /**
     * Re-fetches all critical data relating to this specific PiggyBank.
     * Grabs underlying transactions, current balance totals, and external categories/PiggyBanks for dropdowns.
     */
    const loadData = async () => {
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
    };

    useEffect(() => {
        loadData();
    }, [id]);

    /**
     * Primary form submission handler for injecting new transactions.
     * Evaluates whether it's an Income/Expense/Transfer, processes category creation,
     * and finally uploads everything via the `transactionsApi`.
     */
    const handleAddTx = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!id) return;

        let finalAmount = parseFloat(amount);
        if (['expense', 'withdrawal'].includes(type)) finalAmount = -Math.abs(finalAmount);
        if (['income', 'deposit'].includes(type)) finalAmount = Math.abs(finalAmount);

        try {
            // First resolve category
            let finalCategoryName = '';
            if (isCreatingCat && newCatName.trim() !== '') {
                const newCat = await categoriesApi.create(newCatName.trim());
                finalCategoryName = newCat.name;
            } else if (selectedCatId) {
                const cat = categories.find(c => c.id.toString() === selectedCatId);
                if (cat) finalCategoryName = cat.name;
            }

            if (type === 'transfer') {
                if (!targetBankId) {
                    alert('Please select a target Piggy Bank for transfer.');
                    return;
                }
                const amt = Math.abs(parseFloat(amount));
                await transactionsApi.transfer(parseInt(id), parseInt(targetBankId), amt, desc);
            } else {
                let finalDate = undefined;
                if (txDate) {
                    finalDate = new Date(txDate).toISOString();
                }
                await transactionsApi.create(parseInt(id), finalAmount, type, desc, finalCategoryName, finalDate as any);
            }

            setShowAdd(false);
            setAmount('');
            setDesc('');
            setSelectedCatId('');
            setNewCatName('');
            setIsCreatingCat(false);
            setType('expense');
            setTxDate(new Date().toISOString().split('T')[0]);
            loadData();
        } catch (err) {
            console.error("Failed to add transaction", err);
            alert('Failed to add transaction.');
        }
    };

    if (isLoading) return <div className="p-8 text-center text-muted animate-fade-in">Loading...</div>;
    if (!bank) return <div className="p-8 text-center text-danger animate-fade-in">PiggyBank not found.</div>;

    const transferTargets = allBanks.filter(b => b.id !== bank.id);

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
    const cSym = getCurrencySymbol(bank.currency);

    return (
        <div className="container py-8 animate-fade-in">
            <Link to="/" className="inline-flex items-center text-muted hover:text-text-primary transition-colors mb-6">
                <ArrowLeft size={16} className="mr-2" /> Back to Dashboard
            </Link>

            <div className="glass-panel p-8 mb-8">
                <h1 className="text-3xl font-bold mb-2">{bank.name}</h1>
                <p className="text-text-secondary">PiggyBank Details</p>

                <div className="mt-8">
                    <p className="text-text-secondary text-sm font-medium mb-1">Current Balance</p>
                    <h2 className="text-5xl font-bold tracking-tight text-accent-primary">
                        {cSym}{balance?.balance.toFixed(2) || '0.00'}
                    </h2>
                </div>
            </div>

            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-semibold">Transactions</h2>
                <button
                    onClick={() => setShowAdd(!showAdd)}
                    className="btn btn-primary"
                >
                    <Plus size={16} /> Add Transaction
                </button>
            </div>

            {showAdd && (
                <form onSubmit={handleAddTx} className="glass-panel p-6 mb-8 animate-fade-in flex flex-col gap-4">
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
                                <option value="transfer">Transfer</option>
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
                        <button type="button" onClick={() => setShowAdd(false)} className="btn btn-secondary text-sm">Cancel</button>
                        <button type="submit" className="btn btn-primary text-sm">Save Transaction</button>
                    </div>
                </form>
            )}

            <div className="glass-panel overflow-hidden">
                {transactions.length === 0 ? (
                    <div className="p-8 text-center text-muted">No transactions found.</div>
                ) : (
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b border-glass-border">
                                <th className="p-4 text-text-secondary font-medium text-sm">Date</th>
                                <th className="p-4 text-text-secondary font-medium text-sm">Type</th>
                                <th className="p-4 text-text-secondary font-medium text-sm">Category</th>
                                <th className="p-4 text-text-secondary font-medium text-sm">Description</th>
                                <th className="p-4 text-text-secondary font-medium text-sm text-right">Amount</th>
                                <th className="p-4 text-text-secondary font-medium text-sm text-center">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {transactions.map((tx) => {
                                const isIncome = tx.amount > 0 && tx.type !== 'transfer';
                                const isTransfer = tx.type === 'transfer';

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
                                    typeLabel = 'Transfer';
                                    badgeClass = 'bg-accent-light text-accent-primary';
                                    if (tx.amount > 0) {
                                        textClass = 'text-success';
                                    } else {
                                        textClass = 'text-danger';
                                    }
                                }

                                return (
                                    <tr key={tx.id} className="border-b border-glass-border hover:bg-white hover:bg-opacity-5 transition-colors">
                                        <td className="p-4 text-sm whitespace-nowrap">
                                            {new Date(tx.date).toLocaleDateString()}
                                        </td>
                                        <td className="p-4">
                                            <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${badgeClass}`}>
                                                {icon}
                                                {typeLabel}
                                            </div>
                                        </td>
                                        <td className="p-4 text-sm">
                                            {tx.category ? (
                                                <span className="inline-block px-2 py-1 bg-white bg-opacity-5 border border-glass-border rounded text-xs">
                                                    {tx.category}
                                                </span>
                                            ) : '-'}
                                        </td>
                                        <td className="p-4 text-sm text-text-secondary">{tx.description || '-'}</td>
                                        <td className={`p-4 text-right font-medium ${textClass}`}>
                                            {tx.amount > 0 ? '+' : ''}{cSym}{tx.amount.toFixed(2)}
                                        </td>
                                        <td className="p-4 text-center">
                                            <button
                                                onClick={async () => {
                                                    if (window.confirm('Are you sure you want to delete this transaction?')) {
                                                        try {
                                                            await transactionsApi.delete(tx.id);
                                                            loadData();
                                                        } catch (err) {
                                                            console.error(err);
                                                            alert('Failed to delete transaction.');
                                                        }
                                                    }
                                                }}
                                                className="text-text-secondary hover:text-danger p-1 transition-colors"
                                                title="Delete Transaction"
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
        </div>
    );
};
