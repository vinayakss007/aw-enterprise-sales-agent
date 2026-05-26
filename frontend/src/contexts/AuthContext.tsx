import React, { createContext, useCallback, useContext, useEffect, useState, ReactNode } from 'react';
import { authService } from '../services/authService';
import type { User } from '../types';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (name: string, email: string, password: string) => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'es_agent_token';

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const me = await authService.me();
      setUser(me);
    } catch {
      // Token invalid / expired — drop it and stay anonymous. The api
      // interceptor will already have redirected to /login if appropriate.
      localStorage.removeItem(TOKEN_KEY);
      setUser(null);
    }
  }, []);

  // On mount: if we have a token, hydrate the user. Otherwise stay anonymous.
  useEffect(() => {
    const init = async () => {
      const token = localStorage.getItem(TOKEN_KEY);
      if (token) {
        await refreshUser();
      }
      setLoading(false);
    };
    init();
  }, [refreshUser]);

  const login = useCallback(
    async (email: string, password: string) => {
      const { access_token } = await authService.login(email, password);
      localStorage.setItem(TOKEN_KEY, access_token);
      await refreshUser();
    },
    [refreshUser]
  );

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
  }, []);

  const register = useCallback(
    async (name: string, email: string, password: string) => {
      await authService.register(name, email, password);
      // Auto-login so the rest of the app sees a logged-in user.
      await login(email, password);
    },
    [login]
  );

  const value: AuthContextType = {
    user,
    loading,
    login,
    logout,
    register,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
};
