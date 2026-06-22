import { create } from "zustand";
import { api } from "../api/client";
import type { User } from "../api/types";

interface AuthState {
  user: User | null;
  loading: boolean;
  initialized: boolean;
  error: string | null;
  initialize: () => Promise<void>;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  loading: false,
  initialized: false,
  error: null,
  initialize: async () => {
    set({ loading: true });
    try {
      const user = await api.getCurrentUser();
      set({ user, initialized: true, loading: false, error: null });
    } catch {
      set({ user: null, initialized: true, loading: false, error: null });
    }
  },
  login: async (username, password) => {
    set({ loading: true, error: null });
    try {
      const response = await api.login(username, password);
      set({ user: response.user, loading: false, initialized: true });
    } catch (error) {
      set({
        loading: false,
        error: error instanceof Error ? error.message : "Login failed",
      });
      throw error;
    }
  },
  register: async (username, password) => {
    set({ loading: true, error: null });
    try {
      const response = await api.register(username, password);
      set({ user: response.user, loading: false, initialized: true });
    } catch (error) {
      set({
        loading: false,
        error: error instanceof Error ? error.message : "Registration failed",
      });
      throw error;
    }
  },
  logout: async () => {
    await api.logout();
    const user = await api.getCurrentUser().catch(() => null);
    set({ user, error: null, initialized: true });
  },
}));
