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

        // We don't use the JSON apiClient here because FastAPI expects x-www-form-urlencoded for login by default with OAuth2PasswordRequestForm
        const response = await fetch('http://127.0.0.1:8000/api/v1/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData.toString(),
        });

        if (!response.ok) {
            throw new Error('Login failed');
        }
        return response.json();
    },

    /**
     * Registers a new user into the database and returns their profile.
     */
    register: async (username: string, email: string, password: string): Promise<User> => {
        const { data } = await apiClient.post('/auth/register', { username, email, password });
        return data;
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
