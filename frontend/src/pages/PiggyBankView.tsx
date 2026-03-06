import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { piggybanksApi } from '../api/piggybanks';
import { transactionsApi } from '../api/transactions';
import type { Transaction, PiggyBank, Balance } from '../types';
import { ArrowLeft, ArrowUpRight, ArrowDownRight, Plus } from 'lucide-react';

export const PiggyBankView = () => {
    const { id } = useParams<{ id: string }>();
    const [bank, setBank] = useState<PiggyBank | null>(null);
    const [balance, setBalance] = useState<Balance | null>(null);
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    // Form states
    const [showAdd, setShowAdd] = useState(false);
    const [amount, setAmount] = useState('');
    const [type, setType] = useState('deposit');
    const [desc, setDesc] = useState('');
    const [cat, setCat] = useState('');

    const loadData = async () => {
        if (!id) return;
        setIsLoading(true);
        try {
            const pbs = await piggybanksApi.list();
            const currentBank = pbs.find((p: PiggyBank) => p.id === parseInt(id));
            setBank(currentBank || null);

            const bal = await piggybanksApi.getBalance(parseInt(id));
            setBalance(bal);

            const txs = await transactionsApi.list(parseInt(id));
            setTransactions(txs);
        } catch (err) {
            console.error("Failed to load piggy bank", err);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, [id]);

    const handleAddTx = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!id) return;

        let finalAmount = parseFloat(amount);
        if (type === 'withdrawal') finalAmount = -finalAmount;

        try {
            await transactionsApi.create(parseInt(id), finalAmount, desc, cat);
            setShowAdd(false);
            setAmount('');
            setDesc('');
            setCat('');
            loadData();
        } catch (err) {
            console.error("Failed to add transaction", err);
            alert('Failed to add transaction.');
        }
    };

    if (isLoading) return <div className="p-8 text-center text-muted animate-fade-in">Loading...</div>;
    if (!bank) return <div className="p-8 text-center text-danger animate-fade-in">PiggyBank not found.</div>;

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
                        ${balance?.balance.toFixed(2)}
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
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">Type</label>
                            <select
                                className="input-field"
                                value={type}
                                onChange={(e) => setType(e.target.value)}
                            >
                                <option value="deposit">Deposit</option>
                                <option value="withdrawal">Withdrawal</option>
                            </select>
                        </div>
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
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">Category</label>
                            <input
                                type="text"
                                className="input-field"
                                value={cat}
                                onChange={(e) => setCat(e.target.value)}
                                placeholder="e.g. Salary, Rent"
                            />
                        </div>
                        <div>
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
                            </tr>
                        </thead>
                        <tbody>
                            {transactions.map((tx) => {
                                const isDeposit = tx.amount > 0;
                                return (
                                    <tr key={tx.id} className="border-b border-glass-border hover:bg-white hover:bg-opacity-5 transition-colors">
                                        <td className="p-4 text-sm whitespace-nowrap">
                                            {new Date(tx.date).toLocaleDateString()}
                                        </td>
                                        <td className="p-4">
                                            <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${isDeposit ? 'bg-success bg-opacity-10 text-success' : 'bg-danger bg-opacity-10 text-danger'}`}>
                                                {isDeposit ? <ArrowUpRight size={14} className="mr-1" /> : <ArrowDownRight size={14} className="mr-1" />}
                                                {isDeposit ? 'Deposit' : 'Withdrawal'}
                                            </div>
                                        </td>
                                        <td className="p-4 text-sm">{tx.category || '-'}</td>
                                        <td className="p-4 text-sm">{tx.description || '-'}</td>
                                        <td className={`p-4 text-right font-medium ${isDeposit ? 'text-success' : 'text-danger'}`}>
                                            {isDeposit ? '+' : ''}{tx.amount.toFixed(2)}
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
