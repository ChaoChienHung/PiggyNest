import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ChevronLeft, ChevronRight, X } from 'lucide-react';
import type { Transaction } from '../types';
import { formatDate, formatPeriod, isoDatePart, type DateFormat } from '../utils/dates';
import { formatMoney } from '../utils/money';

export interface PeriodTransactionItem {
    transaction: Transaction;
    bankId: number;
    bankName: string;
    bankCurrency: string;
    convertedAmount?: number;
}

interface PeriodTransactionsModalProps {
    period: string;
    scale: 'day' | 'month' | 'year';
    dateFormat: DateFormat;
    displayCurrency: string;
    entries: PeriodTransactionItem[];
    summary?: { income: number; expense: number; balance: number };
    showBankBadge?: boolean;
    onPrev?: () => void;
    onNext?: () => void;
    onClose: () => void;
}

const typeLabel = (txType: string) => {
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

export const PeriodTransactionsModal = ({
    period,
    scale,
    dateFormat,
    displayCurrency,
    entries,
    summary,
    showBankBadge = false,
    onPrev,
    onNext,
    onClose,
}: PeriodTransactionsModalProps) => {
    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key === 'Escape') onClose();
            else if (event.key === 'ArrowLeft' && onPrev) onPrev();
            else if (event.key === 'ArrowRight' && onNext) onNext();
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [onClose, onPrev, onNext]);

    const sortedEntries = [...entries].sort(
        (a, b) =>
            isoDatePart(b.transaction.date).localeCompare(isoDatePart(a.transaction.date))
            || b.transaction.id - a.transaction.id,
    );
    const periodLabel = formatPeriod(period, scale, dateFormat);
    const scaleNoun = scale === 'day' ? 'Day' : scale === 'month' ? 'Month' : 'Year';

    return (
        <div
            className="modal-backdrop"
            role="presentation"
            onClick={(event) => {
                if (event.target === event.currentTarget) onClose();
            }}
        >
            <div
                className="glass-panel utility-modal period-drilldown-modal animate-fade-in"
                role="dialog"
                aria-modal="true"
                aria-labelledby="period-drilldown-title"
            >
                <div className="utility-modal-header">
                    <div>
                        <h3 id="period-drilldown-title" className="text-xl font-bold">
                            {periodLabel}
                        </h3>
                        <p className="text-sm text-text-secondary">
                            {scaleNoun} interval · {sortedEntries.length} transaction{sortedEntries.length === 1 ? '' : 's'}
                        </p>
                    </div>
                    <div className="period-drilldown-nav">
                        <button
                            type="button"
                            className="btn btn-secondary utility-icon-close"
                            onClick={onPrev}
                            disabled={!onPrev}
                            aria-label="Previous period"
                            title="Previous period"
                        >
                            <ChevronLeft size={18} />
                        </button>
                        <button
                            type="button"
                            className="btn btn-secondary utility-icon-close"
                            onClick={onNext}
                            disabled={!onNext}
                            aria-label="Next period"
                            title="Next period"
                        >
                            <ChevronRight size={18} />
                        </button>
                        <button
                            type="button"
                            className="btn btn-secondary utility-icon-close"
                            onClick={onClose}
                            aria-label="Close"
                            title="Close"
                        >
                            <X size={18} />
                        </button>
                    </div>
                </div>

                {summary && (
                    <div className="period-drilldown-summary">
                        <div className="period-drilldown-stat">
                            <span className="text-xs text-text-secondary">Ending balance</span>
                            <strong>{formatMoney(summary.balance, displayCurrency)}</strong>
                        </div>
                        <div className="period-drilldown-stat">
                            <span className="text-xs text-text-secondary">Income</span>
                            <strong className="text-success">{formatMoney(summary.income, displayCurrency)}</strong>
                        </div>
                        <div className="period-drilldown-stat">
                            <span className="text-xs text-text-secondary">Spending</span>
                            <strong className="text-danger">{formatMoney(summary.expense, displayCurrency)}</strong>
                        </div>
                    </div>
                )}

                <div className="utility-modal-body">
                    {sortedEntries.length === 0 ? (
                        <p className="text-muted text-center p-8">No transactions in this period.</p>
                    ) : (
                        <div className="utility-list">
                            {sortedEntries.map(({ transaction: tx, bankId, bankName, bankCurrency, convertedAmount }) => {
                                const isPositive = tx.amount >= 0;
                                const showConverted = showBankBadge && bankCurrency !== displayCurrency && convertedAmount !== undefined;
                                return (
                                    <div key={tx.id} className="utility-card">
                                        <div className="utility-card-main">
                                            <div className="utility-card-info">
                                                <div className="period-drilldown-meta">
                                                    <span className="text-xs font-semibold text-text-secondary">
                                                        {formatDate(tx.date, dateFormat)}
                                                    </span>
                                                    {showBankBadge && (
                                                        <Link
                                                            to={`/piggybanks/${bankId}`}
                                                            className="period-drilldown-bank-link"
                                                            onClick={onClose}
                                                        >
                                                            {bankName}
                                                        </Link>
                                                    )}
                                                    <span className="period-drilldown-chip">
                                                        {tx.category || 'Uncategorized'}
                                                    </span>
                                                    <span className="text-xs text-muted">
                                                        {typeLabel(tx.type)} · #{tx.id}
                                                    </span>
                                                </div>
                                                <p className="font-semibold text-text-primary mt-1">
                                                    {tx.description || tx.category || typeLabel(tx.type)}
                                                </p>
                                            </div>
                                            <div className="period-drilldown-amount">
                                                <strong className={isPositive ? 'text-success' : 'text-danger'}>
                                                    {formatMoney(tx.amount, bankCurrency, true)}
                                                </strong>
                                                {showConverted && (
                                                    <span className="text-xs text-text-secondary">
                                                        ≈ {formatMoney(convertedAmount, displayCurrency, true)}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
