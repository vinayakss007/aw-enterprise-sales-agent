/**
 * Superadmin-only endpoints: platform overview, user management,
 * tenant limits, and tenant deletion.
 */
import { api } from './api';

export interface SuperadminOverview {
  total_tenants: number;
  total_users: number;
  total_leads: number;
  total_campaigns: number;
  total_agent_runs: number;
  total_cost: number;
}

export interface SuperadminUser {
  id: string;
  email: string;
  name: string;
  role: string;
  tenant_id: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TenantLimits {
  max_users?: number;
  max_leads?: number;
  max_campaigns?: number;
  max_agent_runs_per_day?: number;
  max_cost_per_month?: number;
  [key: string]: number | undefined;
}

export const superadminService = {
  async getOverview(): Promise<SuperadminOverview> {
    const response = await api.get<SuperadminOverview>('/superadmin/overview');
    return response.data;
  },

  async listUsers(params?: { skip?: number; limit?: number }): Promise<SuperadminUser[]> {
    const response = await api.get<SuperadminUser[]>('/superadmin/users', { params });
    return response.data;
  },

  async setUserRole(userId: string, role: string): Promise<SuperadminUser> {
    const response = await api.put<SuperadminUser>(`/superadmin/users/${userId}/role`, { role });
    return response.data;
  },

  async activateUser(userId: string): Promise<SuperadminUser> {
    const response = await api.put<SuperadminUser>(`/superadmin/users/${userId}/activate`);
    return response.data;
  },

  async deactivateUser(userId: string): Promise<SuperadminUser> {
    const response = await api.put<SuperadminUser>(`/superadmin/users/${userId}/deactivate`);
    return response.data;
  },

  async getTenantLimits(tenantId: string): Promise<TenantLimits> {
    const response = await api.get<TenantLimits>(`/superadmin/tenants/${tenantId}/limits`);
    return response.data;
  },

  async setTenantLimits(tenantId: string, limits: TenantLimits): Promise<TenantLimits> {
    const response = await api.put<TenantLimits>(`/superadmin/tenants/${tenantId}/limits`, limits);
    return response.data;
  },

  async deleteTenant(tenantId: string): Promise<{ message: string }> {
    const response = await api.delete<{ message: string }>(`/superadmin/tenants/${tenantId}`);
    return response.data;
  },
};

export default superadminService;
