import { apiClient } from './client';
import type { Transaction } from '../types';

export const transactionsApi = {
    /**
     * Lists all transactions belonging to a specific PiggyBank id.
     */
    list: async (piggyBankId: number): Promise<Transaction[]> => {
        const { data } = await apiClient.get(`/piggy-banks/${piggyBankId}/transactions`);
        return data;
    },
    /**
     * Dispatches a unified payload to create a localized PiggyBank transaction.
     */
    create: async (piggyBankId: number, amount: number, type: string, description: string, category: string, date: string) => {
        const { data } = await apiClient.post(`/piggy-banks/${piggyBankId}/transactions`, {
            amount,
            type,
            description,
            category,
            date,
        });
        return data;
    },
    /**
     * Instructs the backend to execute an inter-PiggyBank fund transfer.
     */
    transfer: async (sourceId: number, targetId: number, amount: number, description: string) => {
        const { data } = await apiClient.post('/transfers', {
            source_piggy_bank_id: sourceId,
            target_piggy_bank_id: targetId,
            amount,
            description,
        });
        return data;
    },
    /**
     * Hard-deletes a single transaction by its primary key.
     */
    delete: async (transactionId: number): Promise<void> => {
        await apiClient.delete(`/transactions/${transactionId}`);
    }
};
