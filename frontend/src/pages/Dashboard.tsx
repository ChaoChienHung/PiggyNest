import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { piggybanksApi } from '../api/piggybanks';
import type { PiggyBank, Balance } from '../types';
import { Plus, Wallet, LogOut, ArrowRight, Settings } from 'lucide-react';
import { StatisticsCharts } from '../components/StatisticsCharts';

interface PiggyBankWithBalance extends PiggyBank {
    details?: Balance;
}

/**
 * Primary user interface displayed upon successful login.
 * Manages the aggregation of PiggyBanks, total Net Worth calculation, and Analytics mounting.
 */
export const Dashboard = () => {
    const { user, logout } = useAuth();

    const [piggyBanks, setPiggyBanks] = useState<PiggyBankWithBalance[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [showCreate, setShowCreate] = useState(false);
    const [newName, setNewName] = useState('');
    const [newCurrency, setNewCurrency] = useState('USD');

    /**
     * Fetches all PiggyBanks belonging to the user and their respective current balances.
     * Maps these together into the `piggyBanks` state array.
     */
    const loadData = async () => {
        try {
            const pbs = await piggybanksApi.list();

            // Fetch balance for each piggy bank
            const pbsWithBalance = await Promise.all(
                pbs.map(async (pb: PiggyBank) => {
                    const details = await piggybanksApi.getBalance(pb.id);
                    return { ...pb, details };
                })
            );

            setPiggyBanks(pbsWithBalance);
        } catch (err) {
            console.error("Failed to load dashboard data", err);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    /**
     * Form submission handler to dispatch the create API call for a new PiggyBank.
     * Prevents empty names and re-fetches the Dashboard state upon success.
     */
    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newName.trim()) return;

        try {
            await piggybanksApi.create(newName, newCurrency);
            setNewName('');
            setNewCurrency('USD');
            setShowCreate(false);
            loadData();
        } catch (err) {
            console.error("Failed to create piggy bank", err);
            alert('Failed to create. Use alphanumeric names.');
        }
    };

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

    /**
     * Compute total user balance separated by currency to prevent inaccurate cross-currency math.
     */
    const balancesByCurrency = piggyBanks.reduce((acc, pb) => {
        const bal = pb.details?.balance || 0;
        acc[pb.currency] = (acc[pb.currency] || 0) + bal;
        return acc;
    }, {} as Record<string, number>);

    if (isLoading) {
        return <div className="p-8 text-center text-muted animate-fade-in">Loading dashboard...</div>;
    }

    return (
        <div className="container py-8 animate-fade-in">
            <header className="flex justify-between items-center mb-10">
                <div>
                    <h1 className="text-3xl font-bold">Dashboard</h1>
                    <p className="text-muted mt-1">Welcome back, {user?.username || user?.email}</p>
                </div>
                <div className="flex gap-3">
                    <Link to="/settings" className="btn btn-secondary text-sm">
                        <Settings size={16} /> Settings
                    </Link>
                    <button onClick={logout} className="btn btn-secondary text-sm">
                        <LogOut size={16} /> Logout
                    </button>
                </div>
            </header>

            <div className="glass-panel p-8 mb-10 flex items-center justify-between">
                <div>
                    <p className="text-text-secondary text-sm font-medium mb-1">Total Net Worth</p>
                    {Object.entries(balancesByCurrency).length > 0 ? (
                        Object.entries(balancesByCurrency).map(([currency, total]) => (
                            <h2 key={currency} className="text-4xl font-bold tracking-tight mb-2">
                                {getCurrencySymbol(currency)}{total.toFixed(2)}
                            </h2>
                        ))
                    ) : (
                        <h2 className="text-4xl font-bold tracking-tight">$0.00</h2>
                    )}
                </div>
                <div className="p-4 bg-accent-light rounded-2xl text-accent-primary">
                    <Wallet size={32} />
                </div>
            </div>

            <StatisticsCharts />

            <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-semibold">Your PiggyBanks</h3>
                <button
                    onClick={() => setShowCreate(!showCreate)}
                    className="btn btn-primary text-sm py-2"
                >
                    <Plus size={16} /> New PiggyBank
                </button>
            </div>

            {showCreate && (
                <form onSubmit={handleCreate} className="glass-panel p-6 mb-8 flex gap-4 items-end animate-fade-in">
                    <div className="flex-1 flex gap-2">
                        <div className="flex-1">
                            <label className="block text-sm font-medium text-text-secondary mb-1">PiggyBank Name</label>
                            <input
                                type="text"
                                required
                                className="input-field"
                                value={newName}
                                onChange={(e) => setNewName(e.target.value)}
                                placeholder="e.g. Travel Fund"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">Currency</label>
                            <select
                                className="input-field w-24"
                                value={newCurrency}
                                onChange={(e) => setNewCurrency(e.target.value)}
                            >
                                <option value="USD">USD ($)</option>
                                <option value="EUR">EUR (€)</option>
                                <option value="GBP">GBP (£)</option>
                                <option value="JPY">JPY (¥)</option>
                                <option value="NTD">NTD (NT$)</option>
                                <option value="SGD">SGD (S$)</option>
                            </select>
                        </div>
                    </div>
                    <button type="submit" className="btn btn-primary">Create</button>
                    <button type="button" onClick={() => setShowCreate(false)} className="btn btn-secondary">Cancel</button>
                </form>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {piggyBanks.map((pb) => (
                    <Link
                        key={pb.id}
                        to={`/piggybanks/${pb.id}`}
                        className="glass-panel p-6 hover:border-accent-primary transition-all duration-300 group block"
                    >
                        <div className="flex justify-between items-start mb-4">
                            <h4 className="font-semibold text-lg">{pb.name}</h4>
                            <ArrowRight size={18} className="text-muted group-hover:text-accent-primary transition-colors" />
                        </div>

                        <p className="text-text-secondary text-sm mb-1">Current Balance</p>
                        <p className="text-2xl font-bold">{getCurrencySymbol(pb.currency)}{pb.details?.balance.toFixed(2) || '0.00'}</p>

                        <div className="flex justify-between items-center mt-4 mt-auto">
                            <p className="text-xs text-muted">
                                {pb.details?.transaction_count || 0} transactions
                            </p>
                            <button
                                onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    if (window.confirm(`Are you sure you want to delete "${pb.name}" and all its transactions?`)) {
                                        piggybanksApi.remove(pb.id)
                                            .then(() => loadData())
                                            .catch((err: any) => {
                                                console.error(err);
                                                alert("Failed to delete piggy bank");
                                            });
                                    }
                                }}
                                className="text-muted hover:text-danger p-1 rounded transition-colors"
                                title="Delete PiggyBank"
                            >
                                ✕
                            </button>
                        </div>
                    </Link>
                ))}
                {piggyBanks.length === 0 && !showCreate && (
                    <div className="col-span-full text-center p-12 glass-panel border-dashed text-text-muted">
                        <p>You don't have any PiggyBanks yet. Create one to start saving!</p>
                    </div>
                )}
            </div>
        </div>
    );
};
