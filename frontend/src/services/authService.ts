/**
 * Authentication endpoints.
 *
 * Notable: ``/auth/token`` is OAuth2's password flow — it expects
 * ``application/x-www-form-urlencoded`` (with ``username`` and ``password``
 * fields), not JSON. Sending JSON gets a 422 back. We use URLSearchParams
 * here to format the body correctly.
 */
import { api } from './api';
import type { TokenResponse, User } from '../types';

export const authService = {
  async login(email: string, password: string): Promise<TokenResponse> {
    const body = new URLSearchParams();
    body.append('username', email);
    body.append('password', password);
    const response = await api.post<TokenResponse>('/auth/token', body, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return response.data;
  },

  async register(name: string, email: string, password: string): Promise<User> {
    const response = await api.post<User>('/auth/register', { name, email, password });
    return response.data;
  },

  async me(): Promise<User> {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },
};

export default authService;
