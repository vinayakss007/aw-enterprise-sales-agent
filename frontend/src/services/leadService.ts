/**
 * Lead CRUD endpoints.
 *
 * Mirrors ``/api/v1/customer/leads/``. Note that ``delete`` archives the
 * lead (sets status="archived") rather than hard-deleting — the backend
 * does the soft-delete; we surface it as ``archive`` here so the UI is
 * honest about what's happening.
 */
import { api } from './api';
import type { Lead, LeadCreate, LeadUpdate } from '../types';

export const leadService = {
  async list(params?: { skip?: number; limit?: number }): Promise<Lead[]> {
    const response = await api.get<Lead[]>('/customer/leads/', { params });
    return response.data;
  },

  async get(leadId: string): Promise<Lead> {
    const response = await api.get<Lead>(`/customer/leads/${leadId}`);
    return response.data;
  },

  async create(payload: LeadCreate): Promise<Lead> {
    const response = await api.post<Lead>('/customer/leads/', payload);
    return response.data;
  },

  async update(leadId: string, payload: LeadUpdate): Promise<Lead> {
    const response = await api.put<Lead>(`/customer/leads/${leadId}`, payload);
    return response.data;
  },

  async archive(leadId: string): Promise<{ message: string }> {
    const response = await api.delete<{ message: string }>(`/customer/leads/${leadId}`);
    return response.data;
  },
};

export default leadService;
