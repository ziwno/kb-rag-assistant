import { create } from "zustand";
import { persist } from "zustand/middleware";

// 供 axios 拦截器读取的独立 token key (避免持久化 JSON 解析)
export const TOKEN_KEY = "kb-token";

export interface AuthUser {
  id: string;
  username: string;
  email: string;
}

interface AuthState {
  token: string | null;
  user: AuthUser | null;
  setAuth: (token: string, user: AuthUser) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => {
        if (typeof window !== "undefined") {
          window.localStorage.setItem(TOKEN_KEY, token);
        }
        set({ token, user });
      },
      logout: () => {
        if (typeof window !== "undefined") {
          window.localStorage.removeItem(TOKEN_KEY);
        }
        set({ token: null, user: null });
      },
    }),
    { name: "kb-auth" }
  )
);
