/**
 * Admin-only endpoints: tenants, users, usage metrics, campaign worker tick,
 * audit log read + chain verification.
 */
import { api } from './api';
import type { Tenant, UsageMetrics, User, WorkerTickResult } from '../types';

export interface AuditLogEntry {
  id: number;
  timestamp: string;
  tenant_id: string;
  user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string;
  changes_before: Record<string, unknown> | null;
  changes_after: Record<string, unknown> | null;
  ip_address: string | null;
  user_agent: string | null;
  previous_hash: string | null;
  current_hash: string | null;
}

export interface AuditChainResult {
  verified: boolean;
  count: number;
  broken_at: number[];
}

export const adminService = {
  // Tenants
  async listTenants(params?: { skip?: number; limit?: number }): Promise<Tenant[]> {
    const response = await api.get<Tenant[]>('/admin/tenants/', { params });
    return response.data;
  },
  async getTenant(tenantId: string): Promise<Tenant> {
    const response = await api.get<Tenant>(`/admin/tenants/${tenantId}`);
    return response.data;
  },
  async suspendTenant(tenantId: string) {
    const response = await api.post(`/admin/tenants/${tenantId}/suspend`);
    return response.data;
  },
  async activateTenant(tenantId: string) {
    const response = await api.post(`/admin/tenants/${tenantId}/activate`);
    return response.data;
  },

  // Users
  async listUsers(params?: { skip?: number; limit?: number }): Promise<User[]> {
    const response = await api.get<User[]>('/admin/users/', { params });
    return response.data;
  },
  async getUser(userId: string): Promise<User> {
    const response = await api.get<User>(`/admin/users/${userId}`);
    return response.data;
  },

  // Usage
  async getUsage(params?: {
    start_date?: string;
    end_date?: string;
    granularity?: 'hour' | 'day' | 'week' | 'month';
  }): Promise<UsageMetrics> {
    const response = await api.get<UsageMetrics>('/admin/usage/', { params });
    return response.data;
  },

  // Campaign worker tick
  async tickCampaignWorker(batchSize: number = 100): Promise<WorkerTickResult> {
    const response = await api.post<WorkerTickResult>(
      '/admin/campaigns/tick',
      null,
      { params: { batch_size: batchSize } }
    );
    return response.data;
  },

  // Audit
  async listAuditLogs(params?: {
    action?: string;
    resource_type?: string;
    user_id?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
  }): Promise<AuditLogEntry[]> {
    const response = await api.get<AuditLogEntry[]>('/admin/audit/', { params });
    return response.data;
  },

  async verifyAuditChain(): Promise<AuditChainResult> {
    const response = await api.get<AuditChainResult>('/admin/audit/verify');
    return response.data;
  },
};

export default adminService;
