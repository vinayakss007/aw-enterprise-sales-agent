/**
 * agentService tests — agent_type is a query param on the executeAgent
 * endpoint, not a request body field. Lock that in.
 */
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { agentService } from '../agentService';
import { api } from '../api';

vi.mock('../api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('agentService.executeAgent', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it('passes agent_type as a query param, not a body field', async () => {
    (api.post as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { id: 'e1' },
    });
    await agentService.executeAgent('lead-1', 'outreach');
    const [path, body, options] = (api.post as unknown as ReturnType<typeof vi.fn>).mock
      .calls[0];
    expect(path).toBe('/customer/agent/execute/lead-1');
    expect(body).toBeNull();
    expect(options).toEqual({ params: { agent_type: 'outreach' } });
  });

  it('defaults agent_type to "research"', async () => {
    (api.post as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: {},
    });
    await agentService.executeAgent('lead-1');
    const [, , options] = (api.post as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(options.params.agent_type).toBe('research');
  });
});

describe('agentService.listExecutions', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it('returns the array directly (no envelope)', async () => {
    (api.get as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: [{ id: 'e1' }, { id: 'e2' }],
    });
    const list = await agentService.listExecutions();
    expect(list).toHaveLength(2);
    expect(api.get).toHaveBeenCalledWith('/customer/agent/executions', {
      params: undefined,
    });
  });
});
