import { useEffect, useState } from 'react';
import { piggybanksApi } from '../api/piggybanks';
import { transactionsApi } from '../api/transactions';
import type { PiggyBank, Transaction } from '../types';
import type { LedgerEntry } from '../utils/ledgerAnalytics';

export const useLedgerEntries = () => {
    const [banks, setBanks] = useState<PiggyBank[]>([]);
    const [entries, setEntries] = useState<LedgerEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        let active = true;
        piggybanksApi.list().then(async (loaded: PiggyBank[]) => {
            const transactions = await Promise.all(loaded.map(bank => transactionsApi.list(bank.id)));
            if (active) {
                setBanks(loaded);
                setEntries(loaded.flatMap((bank, index) => (transactions[index] as Transaction[]).map(transaction => ({ bank, transaction }))));
            }
        }).catch(err => {
            console.error('Could not load analytics ledger', err);
            if (active) setError('Could not load analytics.');
        }).finally(() => {
            if (active) setLoading(false);
        });
        return () => { active = false; };
    }, []);

    return { banks, entries, loading, error };
};
