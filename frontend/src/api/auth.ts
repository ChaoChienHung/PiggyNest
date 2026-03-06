import { apiClient } from './client';
import type { User } from '../types';

export const authApi = {
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

    register: async (email: string, password: string): Promise<User> => {
        const { data } = await apiClient.post('/auth/register', { email, password });
        return data;
    },

    testToken: async (): Promise<User> => {
        const { data } = await apiClient.post('/auth/test-token');
        return data;
    }
};
