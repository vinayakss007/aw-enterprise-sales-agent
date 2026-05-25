import axios, { AxiosInstance } from 'axios';

// Get API base URL from environment
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('es_agent_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor — on 401, drop the (now-invalid) token and bounce
// back to /login. Skip the redirect on the auth endpoints themselves so the
// LoginPage can show the inline error message instead of an instant reload.
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error.response?.status;
    const url: string | undefined = error.config?.url;
    const isAuthCall = !!url && (url.includes('/auth/token') || url.includes('/auth/register'));
    if (status === 401 && !isAuthCall && typeof window !== 'undefined') {
      localStorage.removeItem('es_agent_token');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export { api };
export default api;