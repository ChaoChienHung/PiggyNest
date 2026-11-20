import { apiClient } from './client';
import type { AppNotification, NotificationListResponse } from '../types';

export const notificationsApi = {
    list: async (): Promise<NotificationListResponse> => {
        const res = await apiClient.get('/notifications');
        return res.data;
    },
    markRead: async (id: number): Promise<AppNotification> => {
        const res = await apiClient.put(`/notifications/${id}/read`);
        return res.data;
    },
    markAllRead: async (): Promise<{ updated_count: number }> => {
        const res = await apiClient.post('/notifications/read-all');
        return res.data;
    },
    delete: async (id: number): Promise<void> => {
        await apiClient.delete(`/notifications/${id}`);
    },
};
