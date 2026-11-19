import { apiClient } from './client';
import type { Transaction } from '../types';

export interface TransactionChanges {
    amount?: number;
    counterpart_amount?: number;
    type?: string;
    description?: string | null;
    category?: string | null;
    date?: string;
}

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
    create: async (piggyBankId: number, amount: number, type: string, description: string, category: string, date?: string) => {
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
    transfer: async (sourceId: number, targetId: number, amount: number, description: string, receivedAmount?: number, date?: string) => {
        const { data } = await apiClient.post('/transfers', {
            source_piggy_bank_id: sourceId,
            target_piggy_bank_id: targetId,
            amount,
            received_amount: receivedAmount,
            description,
            date,
        });
        return data;
    },
    getTransfer: async (transactionId: string): Promise<{ debit: Transaction; credit: Transaction }> => {
        const { data } = await apiClient.get(`/transfers/${transactionId}`);
        return data;
    },
    /**
     * Updates an existing transaction.
     */
    update: async (transactionId: number, changes: TransactionChanges): Promise<Transaction> => {
        const { data } = await apiClient.put(`/transactions/${transactionId}`, changes);
        return data;
    },
    /**
     * Deletes an entry by its primary key; the API also removes its transfer pair.
     */
    delete: async (transactionId: number): Promise<void> => {
        await apiClient.delete(`/transactions/${transactionId}`);
    },
    /**
     * Updates the category for multiple non-transfer transactions atomically.
     */
    bulkUpdateCategory: async (transactionIds: number[], category: string | null): Promise<{ updated_count: number; category: string | null }> => {
        const { data } = await apiClient.post('/transactions/bulk-category', {
            transaction_ids: transactionIds,
            category,
        });
        return data;
    },
    /**
     * Deletes multiple transactions atomically; removes both sides of any PiggyBank transfer.
     */
    bulkDelete: async (transactionIds: number[]): Promise<{ success: boolean; deleted_count: number }> => {
        const { data } = await apiClient.post('/transactions/bulk-delete', {
            transaction_ids: transactionIds,
        });
        return data;
    }
};
