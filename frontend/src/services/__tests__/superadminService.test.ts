/**
 * superadminService tests — verifies correct HTTP calls to the backend.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { superadminService } from '../superadminService';
import { api } from '../api';

vi.mock('../api', () => ({
  api: {
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('superadminService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('getOverview GETs /superadmin/overview', async () => {
    const mockData = {
      total_tenants: 5,
      total_users: 20,
      total_leads: 100,
      total_campaigns: 10,
      total_agent_runs: 50,
      total_cost: 123.45,
    };
    (api.get as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockData });

    const result = await superadminService.getOverview();
    expect(result).toEqual(mockData);
    expect(api.get).toHaveBeenCalledWith('/superadmin/overview');
  });

  it('listUsers GETs /superadmin/users with params', async () => {
    const mockUsers = [{ id: 'u1', email: 'a@b.com', role: 'admin' }];
    (api.get as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockUsers });

    const params = { skip: 0, limit: 50 };
    const result = await superadminService.listUsers(params);
    expect(result).toEqual(mockUsers);
    expect(api.get).toHaveBeenCalledWith('/superadmin/users', { params });
  });

  it('setUserRole PUTs to /superadmin/users/{id}/role with body', async () => {
    const mockResponse = { id: 'u1', email: 'a@b.com', role: 'admin' };
    (api.put as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockResponse });

    const result = await superadminService.setUserRole('u1', 'admin');
    expect(result).toEqual(mockResponse);
    expect(api.put).toHaveBeenCalledWith('/superadmin/users/u1/role', { role: 'admin' });
  });

  it('setTenantLimits PUTs to /superadmin/tenants/{id}/limits', async () => {
    const limits = { max_leads: 500, max_campaigns: 10 };
    const mockResponse = { tenant_id: 't1', name: 'Test', limits };
    (api.put as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockResponse });

    const result = await superadminService.setTenantLimits('t1', limits);
    expect(result).toEqual(mockResponse);
    expect(api.put).toHaveBeenCalledWith('/superadmin/tenants/t1/limits', limits);
  });
});
