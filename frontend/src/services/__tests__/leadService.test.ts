/**
 * leadService tests. The biggest correctness concern is that the URLs are
 * correct (trailing slashes matter — the FastAPI router defines /leads/),
 * and that the methods compose as expected.
 */
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { leadService } from '../leadService';
import { api } from '../api';

vi.mock('../api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

const fakeLead = (overrides: Record<string, unknown> = {}) => ({
  id: 'l1',
  tenant_id: 't1',
  user_id: 'u1',
  status: 'new',
  source: 'agent',
  created_at: '',
  updated_at: '',
  ...overrides,
});

describe('leadService', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it('list() GETs /customer/leads/ with pagination params', async () => {
    (api.get as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: [fakeLead()],
    });
    const leads = await leadService.list({ skip: 10, limit: 20 });
    expect(leads).toHaveLength(1);
    expect(api.get).toHaveBeenCalledWith('/customer/leads/', {
      params: { skip: 10, limit: 20 },
    });
  });

  it('create() POSTs to /customer/leads/', async () => {
    (api.post as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: fakeLead({ email: 'lead@target.test' }),
    });
    const created = await leadService.create({ email: 'lead@target.test' });
    expect(created.email).toBe('lead@target.test');
    expect(api.post).toHaveBeenCalledWith('/customer/leads/', {
      email: 'lead@target.test',
    });
  });

  it('update() PUTs to /customer/leads/:id', async () => {
    (api.put as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: fakeLead({ status: 'qualified' }),
    });
    const updated = await leadService.update('l1', { status: 'qualified' });
    expect(updated.status).toBe('qualified');
    expect(api.put).toHaveBeenCalledWith('/customer/leads/l1', {
      status: 'qualified',
    });
  });

  it('archive() DELETEs /customer/leads/:id', async () => {
    (api.delete as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { message: 'Lead archived successfully' },
    });
    const result = await leadService.archive('l1');
    expect(result.message).toMatch(/archived/);
    expect(api.delete).toHaveBeenCalledWith('/customer/leads/l1');
  });
});
