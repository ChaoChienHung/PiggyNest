import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import { piggybanksApi } from '../api/piggybanks';
import type { PiggyBank, Balance } from '../types';
import { Plus, LogOut, ArrowRight, Settings, Eye, EyeOff } from 'lucide-react';
import { FloatingTools } from '../components/FloatingTools';
import { ThemedSelect } from '../components/ThemedSelect';
import { SettingsDialog } from '../components/SettingsDialog';
import { ConfirmModal, type ModalVariant } from '../components/ConfirmModal';
import { formatMoney } from '../utils/money';
import { useRates } from '../context/useRates';
import { convertAmount, displayCurrencyOptions } from '../utils/currency';
import { authApi } from '../api/auth';

interface PiggyBankWithBalance extends PiggyBank {
    details?: Balance;
}

/**
 * Primary user interface displayed upon successful login.
 * Manages the aggregation of PiggyBanks, total Net Worth calculation, and Analytics mounting.
 */
export const Dashboard = () => {
    const { user, logout, updateUser } = useAuth();
    const { rates, isLoading: ratesLoading } = useRates();

    const [piggyBanks, setPiggyBanks] = useState<PiggyBankWithBalance[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [showCreate, setShowCreate] = useState(false);
    const [newName, setNewName] = useState('');
    const [newCurrency, setNewCurrency] = useState('USD');
    const [settingsOpen, setSettingsOpen] = useState(false);
    const settingsButtonRef = React.useRef<HTMLButtonElement>(null);

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

    /** Sum original balances by currency before converting each currency group. */
    const balancesByCurrency = piggyBanks.reduce((acc, pb) => {
        const bal = pb.details?.balance || 0;
        acc[pb.currency] = (acc[pb.currency] || 0) + bal;
        return acc;
    }, {} as Record<string, number>);
    const displayCurrency = user?.display_currency ?? 'NTD';
    const currencyRows = Object.entries(balancesByCurrency).map(([currency, original]) => ({
        currency, original, converted: convertAmount(original, currency, displayCurrency, rates),
    })).sort((a, b) => (b.converted?.amount ?? -Infinity) - (a.converted?.amount ?? -Infinity));
    const missingRates = currencyRows.filter(row => !row.converted).map(row => row.currency);
    const netWorth = missingRates.length === 0 ? currencyRows.reduce((sum, row) => sum + (row.converted?.amount ?? 0), 0) : null;
    const hidden = user?.net_worth_hidden ?? false;
    const rateTooltip = currencyRows.map(row => row.converted && row.currency !== displayCurrency
        ? `${row.currency}: ${row.converted.explanation}; set ${row.converted.updatedAt}` : '').filter(Boolean).join('\n');
    const convertedByBank = new Map(piggyBanks.map(bank => [bank.id,
        convertAmount(bank.details?.balance ?? 0, bank.currency, displayCurrency, rates)]));

    const changeDisplayCurrency = async (currency: string) => {
        try { updateUser(await authApi.updateDisplayCurrency(currency)); }
        catch (error) { console.error('Could not save display currency', error); }
    };
    const toggleNetWorth = async () => {
        try { updateUser(await authApi.updateNetWorthHidden(!hidden)); }
        catch (error) { console.error('Could not save net worth visibility', error); }
    };

    if (isLoading) {
        return <div className="p-8 text-center text-muted animate-fade-in">Loading dashboard...</div>;
    }

    return (
        <div className="container page-layout-container animate-fade-in">
            <header className="flex justify-between items-center mb-10 dashboard-header">
                <div>
                    <h1 className="dashboard-title">Dashboard</h1>
                    <p className="welcome-subtext">Welcome back, {user?.username || user?.email}</p>
                </div>
                <div className="flex gap-3 dashboard-header-actions">
                    <button ref={settingsButtonRef} type="button" onClick={() => setSettingsOpen(true)} className="btn btn-secondary dashboard-nav-btn">
                        <Settings size={18} /> Settings
                    </button>
                    <button onClick={logout} className="btn btn-secondary dashboard-nav-btn">
                        <LogOut size={18} /> Logout
                    </button>
                </div>
            </header>

            <div className="glass-panel p-8 mb-10 networth-card">
                <div className="networth-main">
                    <p className="networth-label">Total Net Worth</p>
                    <div className="networth-headline">
                        <h2 className="networth-amount" title={!hidden ? rateTooltip : undefined}>
                            {hidden ? '****' : ratesLoading ? 'Loading rates…' : netWorth === null ? 'Rate needed' : formatMoney(netWorth, displayCurrency)}
                        </h2>
                        <ThemedSelect
                            ariaLabel="Net worth display currency"
                            className="networth-currency-select"
                            value={displayCurrency}
                            onChange={changeDisplayCurrency}
                            options={displayCurrencyOptions(piggyBanks.map(bank => bank.currency), displayCurrency)}
                        />
                        <button type="button" className="btn btn-secondary networth-eye" onClick={toggleNetWorth} aria-label={hidden ? 'Show net worth amounts' : 'Hide net worth amounts'}>
                            {hidden ? <Eye size={18} /> : <EyeOff size={18} />}
                        </button>
                    </div>
                    {!ratesLoading && missingRates.length > 0 && !hidden && <p className="text-sm text-danger">
                        Rate needed for {missingRates.join(', ')}. <button type="button" className="networth-settings-link" onClick={() => setSettingsOpen(true)}>Open Settings</button>
                    </p>}
                    {!ratesLoading && currencyRows.length > 0 && <div className="networth-breakdown">
                        {currencyRows.slice(0, 5).map(row => <div className="networth-breakdown-row" key={row.currency} title={!hidden && row.converted ? `${row.converted.explanation}${row.converted.updatedAt ? `; set ${row.converted.updatedAt}` : ''}` : undefined}>
                            <span>{row.currency}</span>
                            <strong>{hidden ? '****' : formatMoney(row.original, row.currency)}</strong>
                            <span>{hidden ? '****' : netWorth !== null && row.converted && netWorth !== 0 ? `${(row.converted.amount / netWorth * 100).toFixed(1)}%` : '—'}</span>
                        </div>)}
                    </div>}
                </div>
            </div>


            <div className="flex justify-between items-center mb-6">
                <h3 className="dashboard-section-title">Piggy Banks</h3>
                <div className="flex items-center gap-3">
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
                            <ThemedSelect
                                ariaLabel="Currency"
                                className="w-24"
                                value={newCurrency}
                                onChange={setNewCurrency}
                                options={['USD', 'EUR', 'GBP', 'JPY', 'NTD', 'SGD'].map(currency => ({ value: currency, label: currency }))}
                            />
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
                                <p className="font-bold text-text-primary" style={{ fontSize: '1.65rem' }}>{formatMoney(pb.details?.balance ?? 0, pb.currency)}</p>
                                {pb.currency !== displayCurrency && <p className="text-sm text-text-secondary" title={convertedByBank.get(pb.id)?.explanation && convertedByBank.get(pb.id)?.updatedAt
                                    ? `${convertedByBank.get(pb.id)?.explanation}; set ${convertedByBank.get(pb.id)?.updatedAt}` : undefined}>
                                    {ratesLoading ? 'Loading rate…' : convertedByBank.get(pb.id)
                                        ? `≈ ${formatMoney(convertedByBank.get(pb.id)!.amount, displayCurrency)}` : 'Rate needed in Settings'}
                                </p>}

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
                                                        .catch((err: unknown) => {
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

            {!showCreate && <FloatingTools />}

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
