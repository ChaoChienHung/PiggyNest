import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { piggybanksApi } from '../api/piggybanks';
import type { PiggyBank, Balance } from '../types';
import { Plus, Wallet, LogOut, ArrowRight } from 'lucide-react';

interface PiggyBankWithBalance extends PiggyBank {
    details?: Balance;
}

export const Dashboard = () => {
    const { user, logout } = useAuth();

    const [piggyBanks, setPiggyBanks] = useState<PiggyBankWithBalance[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [showCreate, setShowCreate] = useState(false);
    const [newName, setNewName] = useState('');

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

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newName.trim()) return;

        try {
            await piggybanksApi.create(newName);
            setNewName('');
            setShowCreate(false);
            loadData();
        } catch (err) {
            console.error("Failed to create piggy bank", err);
            alert('Failed to create. Use alphanumeric names.');
        }
    };

    const totalBalance = piggyBanks.reduce((sum, pb) => sum + (pb.details?.balance || 0), 0);

    if (isLoading) {
        return <div className="p-8 text-center text-muted animate-fade-in">Loading dashboard...</div>;
    }

    return (
        <div className="container py-8 animate-fade-in">
            <header className="flex justify-between items-center mb-10">
                <div>
                    <h1 className="text-3xl font-bold">Dashboard</h1>
                    <p className="text-muted mt-1">Welcome back, {user?.email}</p>
                </div>
                <button onClick={logout} className="btn btn-secondary text-sm">
                    <LogOut size={16} /> Logout
                </button>
            </header>

            <div className="glass-panel p-8 mb-10 flex items-center justify-between">
                <div>
                    <p className="text-text-secondary text-sm font-medium mb-1">Total Net Worth</p>
                    <h2 className="text-4xl font-bold tracking-tight">${totalBalance.toFixed(2)}</h2>
                </div>
                <div className="p-4 bg-accent-light rounded-2xl text-accent-primary">
                    <Wallet size={32} />
                </div>
            </div>

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
                        <p className="text-2xl font-bold">${pb.details?.balance.toFixed(2) || '0.00'}</p>

                        <p className="text-xs text-muted mt-4 mt-auto">
                            {pb.details?.transaction_count || 0} transactions
                        </p>
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
