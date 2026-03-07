import { apiClient } from './client';

export interface StatRecord {
    period: string;
    currency: string;
    income: number;
    expense: number;
    category_expenses: Record<string, number>;
    category_incomes: Record<string, number>;
}

export const statisticsApi = {
    get: async (timeframe: 'monthly' | 'yearly'): Promise<StatRecord[]> => {
        const { data } = await apiClient.get(`/statistics?timeframe=${timeframe}`);
        return data;
    }
};
