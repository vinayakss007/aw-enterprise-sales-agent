/**
 * knowledgeService tests — locks in the URL shapes including the new
 * ``/lookup`` debug endpoint.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { knowledgeService } from '../knowledgeService';
import { api } from '../api';

vi.mock('../api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('knowledgeService CRUD', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('list() GETs /customer/knowledge/ with params', async () => {
    (api.get as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: [],
    });
    await knowledgeService.list({ active_only: false, limit: 50 });
    expect(api.get).toHaveBeenCalledWith('/customer/knowledge/', {
      params: { active_only: false, limit: 50 },
    });
  });

  it('create() POSTs to /customer/knowledge/', async () => {
    (api.post as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { id: 'k1', title: 'Pricing', content: 'plans...' },
    });
    const created = await knowledgeService.create({
      title: 'Pricing',
      content: 'plans...',
    });
    expect(created.id).toBe('k1');
    expect(api.post).toHaveBeenCalledWith('/customer/knowledge/', {
      title: 'Pricing',
      content: 'plans...',
    });
  });

  it('update() PUTs to /customer/knowledge/:id', async () => {
    (api.put as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { id: 'k1', title: 'Updated', content: 'x' },
    });
    await knowledgeService.update('k1', { title: 'Updated' });
    expect(api.put).toHaveBeenCalledWith('/customer/knowledge/k1', {
      title: 'Updated',
    });
  });

  it('remove() DELETEs /customer/knowledge/:id', async () => {
    (api.delete as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { message: 'archived' },
    });
    const result = await knowledgeService.remove('k1');
    expect(result.message).toMatch(/archived/);
    expect(api.delete).toHaveBeenCalledWith('/customer/knowledge/k1');
  });
});

describe('knowledgeService.lookup', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('GETs /customer/knowledge/lookup with q + limit', async () => {
    (api.get as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: [
        { id: 'k1', title: 'Pricing', content: '...', score: 3.0 },
      ],
    });
    const matches = await knowledgeService.lookup('enterprise pricing', 5);
    expect(matches).toHaveLength(1);
    expect(api.get).toHaveBeenCalledWith('/customer/knowledge/lookup', {
      params: { q: 'enterprise pricing', limit: 5 },
    });
  });

  it('defaults to limit=5', async () => {
    (api.get as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: [],
    });
    await knowledgeService.lookup('foo');
    expect(api.get).toHaveBeenCalledWith('/customer/knowledge/lookup', {
      params: { q: 'foo', limit: 5 },
    });
  });
});
