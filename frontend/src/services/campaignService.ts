/**
 * Campaign CRUD + state-transition endpoints.
 *
 * ``addLeads`` posts ``lead_ids`` as the request body itself (the backend
 * accepts a bare ``list[str]``), not wrapped in an envelope.
 */
import { api } from './api';
import type { Campaign, CampaignCreate, CampaignUpdate } from '../types';

export const campaignService = {
  async list(params?: { skip?: number; limit?: number }): Promise<Campaign[]> {
    const response = await api.get<Campaign[]>('/customer/campaigns/', { params });
    return response.data;
  },

  async get(campaignId: string): Promise<Campaign> {
    const response = await api.get<Campaign>(`/customer/campaigns/${campaignId}`);
    return response.data;
  },

  async create(payload: CampaignCreate): Promise<Campaign> {
    const response = await api.post<Campaign>('/customer/campaigns/', payload);
    return response.data;
  },

  async update(campaignId: string, payload: CampaignUpdate): Promise<Campaign> {
    const response = await api.put<Campaign>(`/customer/campaigns/${campaignId}`, payload);
    return response.data;
  },

  async remove(campaignId: string): Promise<{ message: string }> {
    const response = await api.delete<{ message: string }>(`/customer/campaigns/${campaignId}`);
    return response.data;
  },

  async activate(campaignId: string): Promise<{ message: string }> {
    const response = await api.post<{ message: string }>(`/customer/campaigns/${campaignId}/activate`);
    return response.data;
  },

  async deactivate(campaignId: string): Promise<{ message: string }> {
    const response = await api.post<{ message: string }>(`/customer/campaigns/${campaignId}/deactivate`);
    return response.data;
  },

  async addLeads(campaignId: string, leadIds: string[]) {
    const response = await api.post(`/customer/campaigns/${campaignId}/add-leads`, leadIds);
    return response.data as {
      added_leads: number;
      total_requested: number;
      campaign_id: string;
    };
  },
};

export default campaignService;
