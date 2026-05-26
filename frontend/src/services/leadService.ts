/**
 * Lead CRUD endpoints + bulk + enrichment helpers.
 *
 * Mirrors ``/api/v1/customer/leads/``. Note that ``delete`` archives the
 * lead (sets status="archived") rather than hard-deleting - the backend
 * does the soft-delete; we surface it as ``archive`` here so the UI is
 * honest about what's happening.
 */
import { api } from './api';
import type { Lead, LeadCreate, LeadUpdate } from '../types';

export interface ImportReport {
  created: number;
  updated: number;
  skipped: number;
  errors: { row: number; error: string }[];
}

export interface LeadActivity {
  id: string;
  type: string;
  timestamp: string;
  summary: string;
  details?: Record<string, unknown>;
}

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

  async enrich(leadId: string): Promise<Lead> {
    const response = await api.post<Lead>(`/customer/leads/${leadId}/enrich`);
    return response.data;
  },

  async score(leadId: string): Promise<Lead> {
    const response = await api.post<Lead>(`/customer/leads/${leadId}/score`);
    return response.data;
  },

  async getActivity(leadId: string): Promise<LeadActivity[]> {
    const response = await api.get<LeadActivity[]>(`/customer/leads/${leadId}/activity`);
    return response.data;
  },

  async importCsv(file: File): Promise<ImportReport> {
    const form = new FormData();
    form.append('file', file);
    const response = await api.post<ImportReport>(
      '/customer/leads/import',
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return response.data;
  },

  async exportCsv(): Promise<Blob> {
    const response = await api.get('/customer/leads/export.csv', {
      responseType: 'blob',
    });
    return response.data as Blob;
  },
};

export default leadService;
