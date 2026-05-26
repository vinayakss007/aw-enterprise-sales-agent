/**
 * authService tests — the most important fact to lock down is that login
 * sends OAuth2 form-urlencoded body, not JSON. A previous version sent
 * JSON and got back 422 from FastAPI's OAuth2PasswordRequestForm.
 */
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { authService } from '../authService';
import { api } from '../api';

vi.mock('../api', () => ({
  api: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

describe('authService.login', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('sends form-urlencoded body to /auth/token', async () => {
    (api.post as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { access_token: 't.k', token_type: 'bearer' },
    });

    const result = await authService.login('alice@example.com', 'hunter22');
    expect(result.access_token).toBe('t.k');

    expect(api.post).toHaveBeenCalledTimes(1);
    const [path, body, options] = (api.post as unknown as ReturnType<typeof vi.fn>).mock
      .calls[0];
    expect(path).toBe('/auth/token');
    expect(body).toBeInstanceOf(URLSearchParams);
    const params = body as URLSearchParams;
    expect(params.get('username')).toBe('alice@example.com');
    expect(params.get('password')).toBe('hunter22');
    expect(options).toEqual({
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  });
});

describe('authService.register', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('posts JSON to /auth/register', async () => {
    (api.post as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: {
        id: 'u1',
        email: 'alice@example.com',
        name: 'Alice',
        role: 'owner',
        tenant_id: 't1',
        is_active: true,
        is_verified: false,
        created_at: '',
        updated_at: '',
      },
    });

    const user = await authService.register('Alice', 'alice@example.com', 'hunter22');
    expect(user.email).toBe('alice@example.com');
    expect(api.post).toHaveBeenCalledWith('/auth/register', {
      name: 'Alice',
      email: 'alice@example.com',
      password: 'hunter22',
    });
  });
});

describe('authService.me', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('GETs /auth/me', async () => {
    (api.get as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: {
        id: 'u1',
        email: 'alice@example.com',
        name: 'Alice',
        role: 'owner',
        tenant_id: 't1',
        is_active: true,
        is_verified: true,
        created_at: '',
        updated_at: '',
      },
    });

    const me = await authService.me();
    expect(me.role).toBe('owner');
    expect(api.get).toHaveBeenCalledWith('/auth/me');
  });
});
