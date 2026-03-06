import { apiClient } from './client';
import type { Transaction } from '../types';

export const transactionsApi = {
    list: async (piggyBankId: number): Promise<Transaction[]> => {
        const { data } = await apiClient.get(`/piggy-banks/${piggyBankId}/transactions`);
        return data;
    },
    create: async (piggyBankId: number, amount: number, description: string, category: string) => {
        const { data } = await apiClient.post(`/piggy-banks/${piggyBankId}/transactions`, {
            amount,
            description,
            category,
        });
        return data;
    },
    transfer: async (sourceId: number, targetId: number, amount: number, description: string) => {
        const { data } = await apiClient.post('/transfers', {
            source_piggy_bank_id: sourceId,
            target_piggy_bank_id: targetId,
            amount,
            description,
        });
        return data;
    }
};
