import { apiClient } from './client';
import type { User } from '../types';

export const authApi = {
    /**
     * Authenticates a user and returns a Bearer Token.
     * Uses OAuth2 spec form encoding.
     */
    login: async (email: string, password: string): Promise<{ access_token: string; token_type: string }> => {
        const formData = new URLSearchParams();
        formData.append('username', email); // OAuth2 expects username
        formData.append('password', password);

        const { data } = await apiClient.post('/auth/login', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        });
        return data;
    },

    /**
     * Registers a new user into the database and returns their profile.
     */
    register: async (username: string, email: string, password: string): Promise<User> => {
        const { data } = await apiClient.post('/auth/register', { username, email, password });
        return data;
    },

    remindUsername: async (email: string): Promise<void> => {
        await apiClient.post('/auth/recovery/username', { email });
    },

    requestPasswordReset: async (email: string): Promise<void> => {
        await apiClient.post('/auth/recovery/password', { email });
    },

    confirmPasswordReset: async (email: string, code: string, newPassword: string): Promise<void> => {
        await apiClient.post('/auth/recovery/password/confirm', { email, code, new_password: newPassword });
    },

    /**
     * Diagnostic endpoint. Tests if the current JWT in local storage is unexpired.
     */
    testToken: async (): Promise<User> => {
        const { data } = await apiClient.post('/auth/test-token');
        return data;
    },

    /**
     * Updates the username of the currently authenticated user.
     */
    updateProfile: async (username: string): Promise<User> => {
        const { data } = await apiClient.put('/auth/me', { username });
        return data;
    },

    /**
     * Permanently deletes the authenticated user and ALL of their associated data.
     */
    deleteAccount: async (): Promise<void> => {
        await apiClient.delete('/auth/me');
    }
};
