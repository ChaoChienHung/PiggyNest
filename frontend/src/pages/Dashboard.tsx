import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { piggybanksApi } from '../api/piggybanks';
import type { PiggyBank, Balance } from '../types';
import { Plus, Wallet, LogOut, ArrowRight, Settings, TrendingUp } from 'lucide-react';
import { StatisticsCharts } from '../components/StatisticsCharts';
import { ConfirmModal, type ModalVariant } from '../components/ConfirmModal';

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
    const [showAnalytics, setShowAnalytics] = useState(false);

    // Modal state
    const [modalOpen, setModalOpen] = useState(false);
    const [modalConfig, setModalConfig] = useState<{
        title: string; message: string; variant: ModalVariant;
        confirmText?: string; alertOnly?: boolean;
        onConfirm: () => void;
    }>({ title: '', message: '', variant: 'info', onConfirm: () => {} });

    const showModal = useCallback((cfg: typeof modalConfig) => {
        setModalConfig(cfg);
        setModalOpen(true);
    }, []);
    const closeModal = useCallback(() => setModalOpen(false), []);

    const carouselRef = React.useRef<HTMLDivElement>(null);

    const scrollCarousel = (direction: 'left' | 'right') => {
        if (carouselRef.current) {
            const scrollAmount = direction === 'left' ? -340 : 340;
            carouselRef.current.scrollBy({ left: scrollAmount, behavior: 'smooth' });
        }
    };

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
            showModal({ title: 'Creation Failed', message: 'Failed to create piggy bank. Please use alphanumeric names.', variant: 'warning', alertOnly: true, onConfirm: closeModal });
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
        <div className="container page-layout-container animate-fade-in">
            <header className="flex justify-between items-center mb-10">
                <div>
                    <h1 className="dashboard-title">Dashboard 🐷</h1>
                    <p className="welcome-subtext">Welcome back, {user?.username || user?.email}</p>
                </div>
                <div className="flex gap-3">
                    <Link to="/settings" className="btn btn-secondary dashboard-nav-btn">
                        <Settings size={18} /> Settings
                    </Link>
                    <button onClick={logout} className="btn btn-secondary dashboard-nav-btn">
                        <LogOut size={18} /> Logout
                    </button>
                </div>
            </header>

            <div className="glass-panel p-8 mb-10 flex items-center justify-between">
                <div>
                    <p className="networth-label">Total Net Worth</p>
                    {Object.entries(balancesByCurrency).length > 0 ? (
                        Object.entries(balancesByCurrency).map(([currency, total]) => (
                            <h2 key={currency} className="networth-amount">
                                {getCurrencySymbol(currency)}{total.toFixed(2)}
                            </h2>
                        ))
                    ) : (
                        <h2 className="networth-amount">$0.00</h2>
                    )}
                </div>
                <div className="p-4 bg-accent-light rounded-2xl text-accent-primary" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Wallet size={36} />
                </div>
            </div>

            <StatisticsCharts showAnalytics={showAnalytics} setShowAnalytics={setShowAnalytics} />

            <div className="flex justify-between items-center mb-6">
                <h3 className="dashboard-section-title">Piggy Banks 💰</h3>
                <div className="flex items-center gap-3">
                    {/* Inline Pig Trigger next to New PiggyBank */}
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
                        onClick={() => setShowCreate(!showCreate)}
                        className="btn btn-primary"
                    >
                        <Plus size={18} /> New PiggyBank
                    </button>
                </div>
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
                                style={{ paddingRight: '1.5rem' }}
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

            {piggyBanks.length > 0 ? (
                <div className="carousel-wrapper">
                    {/* Floating Glass Arrows */}
                    <button 
                        onClick={() => scrollCarousel('left')} 
                        className="carousel-arrow left" 
                        title="Scroll Left"
                        type="button"
                    >
                        ⟨
                    </button>
                    <button 
                        onClick={() => scrollCarousel('right')} 
                        className="carousel-arrow right" 
                        title="Scroll Right"
                        type="button"
                    >
                        ⟩
                    </button>

                    {/* Smooth Horizontal Carousel Scrollbar Container */}
                    <div className="carousel-container" ref={carouselRef}>
                        {piggyBanks.map((pb) => (
                            <Link
                                key={pb.id}
                                to={`/piggybanks/${pb.id}`}
                                className="glass-panel hover-bounce p-6 group block carousel-card"
                                style={{ display: 'flex', flexDirection: 'column', minHeight: '190px' }}
                            >
                                <div className="flex justify-between items-start mb-4">
                                    <h4 className="font-semibold text-text-primary" style={{ fontSize: '1.5rem' }}>{pb.name}</h4>
                                    <ArrowRight size={18} className="text-muted group-hover:text-accent-primary transition-colors" />
                                </div>

                                <p className="text-text-secondary mb-1" style={{ fontSize: '1.0rem', fontWeight: 600, textTransform: 'uppercase' as const, letterSpacing: '0.05em' }}>Current Balance</p>
                                <p className="font-bold text-text-primary" style={{ fontSize: '1.65rem' }}>{getCurrencySymbol(pb.currency)}{pb.details?.balance.toFixed(2) || '0.00'}</p>

                                <div className="flex justify-between items-center mt-auto pt-4" style={{ marginTop: 'auto' }}>
                                    <p className="text-muted" style={{ fontSize: '1.0rem' }}>
                                        {pb.details?.transaction_count || 0} transactions
                                    </p>
                                    <button
                                        onClick={(e) => {
                                            e.preventDefault();
                                            e.stopPropagation();
                                            showModal({
                                                title: 'Delete PiggyBank',
                                                message: `Are you sure you want to delete "${pb.name}" and all its transactions? This action cannot be undone.`,
                                                variant: 'danger',
                                                confirmText: 'Delete',
                                                onConfirm: () => {
                                                    closeModal();
                                                    piggybanksApi.remove(pb.id)
                                                        .then(() => loadData())
                                                        .catch((err: any) => {
                                                            console.error(err);
                                                            showModal({ title: 'Error', message: 'Failed to delete piggy bank.', variant: 'danger', alertOnly: true, onConfirm: closeModal });
                                                        });
                                                },
                                            });
                                        }}
                                        className="text-muted hover:text-danger p-1 rounded transition-colors"
                                        title="Delete PiggyBank"
                                        style={{ border: 'none', background: 'none', cursor: 'pointer' }}
                                    >
                                        ✕
                                    </button>
                                </div>
                            </Link>
                        ))}
                    </div>
                </div>
            ) : (
                !showCreate && (
                    <div className="text-center p-12 glass-panel border-dashed text-text-muted mb-10">
                        <p>You don't have any PiggyBanks yet. Create one to start saving!</p>
                    </div>
                )
            )}

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
