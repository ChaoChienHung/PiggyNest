import { apiClient } from './client';

export const piggybanksApi = {
    list: async () => {
        const { data } = await apiClient.get('/piggy-banks');
        return data;
    },
    create: async (name: string) => {
        const { data } = await apiClient.post('/piggy-banks', { name });
        return data;
    },
    getBalance: async (id: number) => {
        const { data } = await apiClient.get(`/piggy-banks/${id}/balance`);
        return data;
    }
};
