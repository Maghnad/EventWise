"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useRouter } from "next/navigation";
import type { LoginRequest, SignupRequest, User } from "@/shared/contracts";
import * as authApi from "./authApi";

/* ==========================================================================
   Context Types
   ========================================================================== */

export interface AuthContextValue {
  user: User | null;
  accessToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (data: LoginRequest) => Promise<void>;
  signup: (data: SignupRequest) => Promise<void>;
  logout: () => void;
  refreshSession: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

/* ==========================================================================
   Provider Component
   ========================================================================== */

export function AuthProvider({
  children,
}: {
  children: React.ReactNode;
}): React.JSX.Element {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  /**
   * Refresh access token in memory using HttpOnly cookie or provided token.
   */
  const refreshSession = useCallback(async (): Promise<boolean> => {
    try {
      const response = await authApi.refreshToken();
      authApi.updateTokens(response.tokens);
      setAccessToken(response.tokens.access_token);
      return true;
    } catch {
      authApi.clearAuthSession();
      setUser(null);
      setAccessToken(null);
      return false;
    }
  }, []);

  /**
   * Initialize in-memory session from HttpOnly session cookie on mount.
   */
  useEffect(() => {
    const initializeAuth = async (): Promise<void> => {
      const storedUser = authApi.getStoredUser();
      if (storedUser) {
        setUser(storedUser);
      }

      // Restore active in-memory access token via secure HttpOnly refresh cookie
      const refreshed = await refreshSession();
      if (refreshed) {
        try {
          const token = authApi.getStoredAccessToken();
          if (token) {
            const freshUser = await authApi.getMe(token);
            setUser(freshUser);
          }
        } catch {
          // Token expired or invalid
        }
      }

      setIsLoading(false);
    };

    void initializeAuth();
  }, [refreshSession]);

  /**
   * Log in user and redirect to dashboard.
   */
  const login = useCallback(
    async (data: LoginRequest): Promise<void> => {
      setIsLoading(true);
      try {
        const response = await authApi.login(data);
        authApi.saveAuthSession(response);
        setUser(response.user);
        setAccessToken(response.tokens.access_token);
        router.push("/dashboard");
      } finally {
        setIsLoading(false);
      }
    },
    [router],
  );

  /**
   * Register new account and redirect to dashboard.
   */
  const signup = useCallback(
    async (data: SignupRequest): Promise<void> => {
      setIsLoading(true);
      try {
        const response = await authApi.signup(data);
        authApi.saveAuthSession(response);
        setUser(response.user);
        setAccessToken(response.tokens.access_token);
        router.push("/dashboard");
      } finally {
        setIsLoading(false);
      }
    },
    [router],
  );

  /**
   * Log out user, purge storage, and navigate to login.
   */
  const logout = useCallback((): void => {
    authApi.clearAuthSession();
    setUser(null);
    setAccessToken(null);
    router.push("/login");
  }, [router]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      accessToken,
      isLoading,
      isAuthenticated: Boolean(user && accessToken),
      login,
      signup,
      logout,
      refreshSession,
    }),
    [user, accessToken, isLoading, login, signup, logout, refreshSession],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/* ==========================================================================
   Hook: useAuth
   ========================================================================== */

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an <AuthProvider>");
  }
  return context;
}
