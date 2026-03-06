import axios from 'axios';

const BACKEND_URL = 'http://127.0.0.1:8000/api/v1';

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
