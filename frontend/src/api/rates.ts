import { apiClient } from './client';

export interface CurrencyRate {
    currency: string;
    rate_to_ntd: number;
    updated_at: string;
}

export const ratesApi = {
    list: async (): Promise<CurrencyRate[]> => {
        const { data } = await apiClient.get('/auth/me/rates');
        return data;
    },
    save: async (currency: string, rateToNtd: number): Promise<CurrencyRate> => {
        const { data } = await apiClient.put(`/auth/me/rates/${currency}`, { rate_to_ntd: rateToNtd });
        return data;
    },
};
