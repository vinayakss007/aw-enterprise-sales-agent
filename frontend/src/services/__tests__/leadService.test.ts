/**
 * leadService tests. Locks in the URL shapes and the new
 * enrich / importCsv / exportCsv methods.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

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

describe('leadService CRUD', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

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

describe('leadService enrichment + bulk', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('enrich() POSTs to /customer/leads/:id/enrich with no body', async () => {
    (api.post as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: fakeLead({ enriched_data: { provider: 'fake', confidence: 0.4 } }),
    });
    const lead = await leadService.enrich('l1');
    expect(api.post).toHaveBeenCalledWith('/customer/leads/l1/enrich');
    expect((lead.enriched_data as Record<string, unknown>).provider).toBe('fake');
  });

  it('importCsv() POSTs FormData with multipart Content-Type', async () => {
    (api.post as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { created: 1, updated: 0, skipped: 0, errors: [] },
    });
    const file = new File(['email\nfoo@bar.test\n'], 'leads.csv', {
      type: 'text/csv',
    });
    const report = await leadService.importCsv(file);
    expect(report.created).toBe(1);

    const [path, body, options] = (api.post as unknown as ReturnType<typeof vi.fn>).mock
      .calls[0];
    expect(path).toBe('/customer/leads/import');
    expect(body).toBeInstanceOf(FormData);
    expect((body as FormData).get('file')).toBe(file);
    expect(options.headers['Content-Type']).toBe('multipart/form-data');
  });

  it('exportCsv() GETs /customer/leads/export.csv as blob', async () => {
    const blob = new Blob(['email\nfoo@bar.test\n'], { type: 'text/csv' });
    (api.get as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: blob,
    });
    const result = await leadService.exportCsv();
    expect(result).toBe(blob);
    expect(api.get).toHaveBeenCalledWith('/customer/leads/export.csv', {
      responseType: 'blob',
    });
  });
});
