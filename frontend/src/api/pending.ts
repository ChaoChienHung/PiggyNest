import { apiClient } from './client';
import type { PendingTransaction, Transaction } from '../types';

export const pendingApi = {
    list: async (status: 'pending' | 'confirmed' | 'all' = 'pending'): Promise<PendingTransaction[]> => {
        const res = await apiClient.get('/pending-transactions', { params: { status } });
        return res.data;
    },
    create: async (payload: {
        piggy_bank_id: number;
        amount: number;
        type: string;
        category?: string | null;
        description?: string | null;
        expected_date?: string | null;
    }): Promise<PendingTransaction> => {
        const res = await apiClient.post('/pending-transactions', payload);
        return res.data;
    },
    update: async (
        id: number,
        payload: {
            piggy_bank_id?: number;
            amount?: number;
            type?: string;
            category?: string | null;
            description?: string | null;
            expected_date?: string | null;
        },
    ): Promise<PendingTransaction> => {
        const res = await apiClient.put(`/pending-transactions/${id}`, payload);
        return res.data;
    },
    confirm: async (
        id: number,
        payload: {
            date?: string;
            amount?: number;
            category?: string | null;
            description?: string | null;
            piggy_bank_id?: number;
        } = {},
    ): Promise<Transaction> => {
        const res = await apiClient.post(`/pending-transactions/${id}/confirm`, payload);
        return res.data;
    },
    delete: async (id: number): Promise<void> => {
        await apiClient.delete(`/pending-transactions/${id}`);
    },
};
