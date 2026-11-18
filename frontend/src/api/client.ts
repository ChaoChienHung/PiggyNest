import axios from 'axios';

export const getApiError = (error: unknown, fallback: string): string => {
    if (axios.isAxiosError(error) && typeof error.response?.data?.detail === 'string') {
        return error.response.data.detail;
    }
    return fallback;
};

const BACKEND_URL = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1').replace(/\/$/, '');

export const apiClient = axios.create({
    baseURL: BACKEND_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('piggy_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('piggy_token');
            // Redirect handled in AuthContext or App routing
        }
        return Promise.reject(error);
    }
);
