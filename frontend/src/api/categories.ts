import { apiClient } from './client';
import type { Category } from '../types';

export const categoriesApi = {
    /**
     * Retrieves all spending categories registered to the logged-in user.
     */
    list: async (): Promise<Category[]> => {
        const { data } = await apiClient.get('/categories');
        return data;
    },
    /**
     * Creates a new categorical tag string.
     */
    create: async (name: string): Promise<Category> => {
        const { data } = await apiClient.post('/categories', { name });
        return data;
    },
    /**
     * Updates/renames an existing category by its ID.
     */
    update: async (id: number, new_name: string): Promise<Category> => {
        const { data } = await apiClient.put(`/categories/${id}`, { new_name });
        return data;
    },
    /**
     * Delete a category by its ID. Note this does not delete transactions containing the string.
     */
    delete: async (id: number): Promise<void> => {
        await apiClient.delete(`/categories/${id}`);
    }
};
