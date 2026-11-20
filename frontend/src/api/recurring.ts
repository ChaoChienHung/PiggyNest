import { apiClient } from './client';
import type { RecurrenceFrequency, RecurrenceStatus, RecurringRule } from '../types';

export const recurringApi = {
    list: async (): Promise<RecurringRule[]> => {
        const res = await apiClient.get('/recurring');
        return res.data;
    },
    create: async (payload: {
        piggy_bank_id: number;
        amount: number;
        type: string;
        category?: string | null;
        description?: string | null;
        frequency: RecurrenceFrequency;
        interval: number;
        start_date: string;
        end_date?: string | null;
        initial_transaction_id?: number;
    }): Promise<RecurringRule> => {
        const res = await apiClient.post('/recurring', payload);
        return res.data;
    },
    update: async (
        id: number,
        payload: {
            amount?: number;
            type?: string;
            category?: string | null;
            description?: string | null;
            frequency?: RecurrenceFrequency;
            interval?: number;
            next_run_date?: string;
            end_date?: string | null;
            status?: RecurrenceStatus;
        },
    ): Promise<RecurringRule> => {
        const res = await apiClient.put(`/recurring/${id}`, payload);
        return res.data;
    },
    runDue: async (asOf?: string): Promise<{ posted_count: number; transaction_ids: number[] }> => {
        const res = await apiClient.post('/recurring/run-due', asOf ? { as_of: asOf } : {});
        return res.data;
    },
    delete: async (id: number): Promise<void> => {
        await apiClient.delete(`/recurring/${id}`);
    },
};
