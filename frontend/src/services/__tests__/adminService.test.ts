/**
 * adminService tests — focused on the new audit endpoints.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

import adminService from '../adminService';
import { api } from '../api';

vi.mock('../api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('adminService.listAuditLogs', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('GETs /admin/audit/ with the supplied filters', async () => {
    (api.get as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: [
        {
          id: 1,
          timestamp: '2026-05-25T00:00:00Z',
          tenant_id: 't1',
          user_id: 'u1',
          action: 'login.success',
          resource_type: 'user',
          resource_id: 'u1',
          changes_before: null,
          changes_after: null,
          ip_address: '1.2.3.4',
          user_agent: null,
          previous_hash: '',
          current_hash: 'abc',
        },
      ],
    });

    const rows = await adminService.listAuditLogs({
      action: 'login.success',
      limit: 10,
    });
    expect(rows).toHaveLength(1);
    expect(api.get).toHaveBeenCalledWith('/admin/audit/', {
      params: { action: 'login.success', limit: 10 },
    });
  });

  it('omits filter params when none provided', async () => {
    (api.get as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: [],
    });
    await adminService.listAuditLogs();
    expect(api.get).toHaveBeenCalledWith('/admin/audit/', { params: undefined });
  });
});

describe('adminService.verifyAuditChain', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('GETs /admin/audit/verify and returns the chain result', async () => {
    (api.get as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { verified: true, count: 5, broken_at: [] },
    });

    const result = await adminService.verifyAuditChain();
    expect(result.verified).toBe(true);
    expect(result.count).toBe(5);
    expect(api.get).toHaveBeenCalledWith('/admin/audit/verify');
  });

  it('surfaces a broken chain with the offending IDs', async () => {
    (api.get as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { verified: false, count: 5, broken_at: [3] },
    });

    const result = await adminService.verifyAuditChain();
    expect(result.verified).toBe(false);
    expect(result.broken_at).toEqual([3]);
  });
});
