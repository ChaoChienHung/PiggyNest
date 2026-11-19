import { apiClient } from './client';

export const piggybanksApi = {
    list: async () => {
        const { data } = await apiClient.get('/piggy-banks');
        return data;
    },
    create: async (name: string, currency: string = "USD") => {
        const { data } = await apiClient.post('/piggy-banks', { name, currency });
        return data;
    },
    getBalance: async (id: number) => {
        const { data } = await apiClient.get(`/piggy-banks/${id}/balance`);
        return data;
    },
    remove: async (id: number) => {
        await apiClient.delete(`/piggy-banks/${id}`);
    },
    setPinned: async (id: number, isPinned: boolean) => {
        const { data } = await apiClient.put(`/piggy-banks/${id}/pin`, { is_pinned: isPinned });
        return data;
    }
};
