/**
 * AuthContext component tests.
 *
 * The big concerns this file pins down:
 *   1. Login flow stores the token + populates ``user`` from /auth/me.
 *   2. Failed login surfaces the error and leaves user null.
 *   3. Logout clears the token and ``user``.
 *   4. On mount, an existing token in localStorage hydrates ``user``.
 *
 * authService is mocked so we don't depend on the network or the api.ts
 * interceptors.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, render, renderHook, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { AuthProvider, useAuth } from '../AuthContext';
import { authService } from '../../services/authService';
import type { User } from '../../types';

vi.mock('../../services/authService', () => ({
  authService: {
    login: vi.fn(),
    register: vi.fn(),
    me: vi.fn(),
  },
}));

const fakeUser: User = {
  id: 'u1',
  email: 'alice@example.com',
  name: 'Alice',
  role: 'owner',
  tenant_id: 't1',
  is_active: true,
  is_verified: true,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

beforeEach(() => {
  localStorage.clear();
  vi.clearAllMocks();
});

afterEach(() => {
  localStorage.clear();
});

describe('AuthProvider initial state', () => {
  it('starts anonymous when there is no token', async () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: ({ children }) => <AuthProvider>{children}</AuthProvider>,
    });
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.user).toBeNull();
    expect(authService.me).not.toHaveBeenCalled();
  });

  it('hydrates user from /auth/me when a token exists in localStorage', async () => {
    localStorage.setItem('es_agent_token', 'existing.jwt');
    (authService.me as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce(fakeUser);

    const { result } = renderHook(() => useAuth(), {
      wrapper: ({ children }) => <AuthProvider>{children}</AuthProvider>,
    });
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(authService.me).toHaveBeenCalledTimes(1);
    expect(result.current.user).toEqual(fakeUser);
  });

  it('drops the token and stays anonymous if /auth/me throws', async () => {
    localStorage.setItem('es_agent_token', 'invalid.jwt');
    (authService.me as unknown as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error('401')
    );

    const { result } = renderHook(() => useAuth(), {
      wrapper: ({ children }) => <AuthProvider>{children}</AuthProvider>,
    });
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.user).toBeNull();
    expect(localStorage.getItem('es_agent_token')).toBeNull();
  });
});

describe('AuthProvider login + logout', () => {
  it('login stores the token, fetches /auth/me, and exposes the user', async () => {
    (authService.login as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      access_token: 'fresh.jwt',
      token_type: 'bearer',
    });
    (authService.me as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce(fakeUser);

    const { result } = renderHook(() => useAuth(), {
      wrapper: ({ children }) => <AuthProvider>{children}</AuthProvider>,
    });
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.login('alice@example.com', 'hunter22');
    });

    expect(authService.login).toHaveBeenCalledWith('alice@example.com', 'hunter22');
    expect(localStorage.getItem('es_agent_token')).toBe('fresh.jwt');
    expect(result.current.user).toEqual(fakeUser);
  });

  it('login rejects when authService.login throws and leaves user null', async () => {
    (authService.login as unknown as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error('Invalid credentials')
    );

    const { result } = renderHook(() => useAuth(), {
      wrapper: ({ children }) => <AuthProvider>{children}</AuthProvider>,
    });
    await waitFor(() => expect(result.current.loading).toBe(false));

    await expect(
      act(async () => {
        await result.current.login('alice@example.com', 'wrong');
      })
    ).rejects.toThrow('Invalid credentials');

    expect(localStorage.getItem('es_agent_token')).toBeNull();
    expect(result.current.user).toBeNull();
  });

  it('logout clears the token and the user', async () => {
    localStorage.setItem('es_agent_token', 'existing.jwt');
    (authService.me as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce(fakeUser);

    const { result } = renderHook(() => useAuth(), {
      wrapper: ({ children }) => <AuthProvider>{children}</AuthProvider>,
    });
    await waitFor(() => expect(result.current.user).toEqual(fakeUser));

    act(() => {
      result.current.logout();
    });

    expect(localStorage.getItem('es_agent_token')).toBeNull();
    expect(result.current.user).toBeNull();
  });
});

describe('AuthProvider in a component tree', () => {
  it('renders the user email after a successful login click', async () => {
    (authService.login as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      access_token: 'jwt',
      token_type: 'bearer',
    });
    (authService.me as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce(fakeUser);

    const Greeter: React.FC = () => {
      const { user, login } = useAuth();
      return user ? (
        <p>Hi {user.email}</p>
      ) : (
        <button onClick={() => login('alice@example.com', 'hunter22')}>Sign in</button>
      );
    };

    render(
      <AuthProvider>
        <Greeter />
      </AuthProvider>
    );

    await screen.findByRole('button', { name: 'Sign in' });
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }));
    expect(await screen.findByText('Hi alice@example.com')).toBeInTheDocument();
  });
});
