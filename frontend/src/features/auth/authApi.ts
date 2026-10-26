/**
 * Authentication API Service and Token Persistence Helpers.
 *
 * Provides typed HTTP calls to /auth endpoints and handles localStorage token storage
 * with automatic token refresh logic.
 */

import { api, setAccessToken, type ApiError } from "@/services/api";
import type {
  AuthResponse,
  AuthTokens,
  LoginRequest,
  RefreshTokenRequest,
  SignupRequest,
  TokenRefreshResponse,
  User,
} from "@/shared/contracts";

/* ==========================================================================
   In-Memory Auth & Non-Sensitive Storage Helpers
   ========================================================================== */

const USER_KEY = "eventwise_user_profile";

export function getStoredAccessToken(): string | null {
  // Security Hardening: Access tokens are never persisted to localStorage
  return null;
}

export function getStoredRefreshToken(): string | null {
  // Security Hardening: Refresh tokens are stored in HttpOnly SameSite=Lax cookies
  return null;
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const userJson = localStorage.getItem(USER_KEY);
  if (!userJson) return null;
  try {
    return JSON.parse(userJson) as User;
  } catch {
    return null;
  }
}

export function saveAuthSession(response: AuthResponse): void {
  setAccessToken(response.tokens.access_token);
  if (typeof window !== "undefined") {
    localStorage.setItem(USER_KEY, JSON.stringify(response.user));
  }
}

export function updateTokens(tokens: AuthTokens): void {
  setAccessToken(tokens.access_token);
}

export function clearAuthSession(): void {
  setAccessToken(null);
  if (typeof window !== "undefined") {
    localStorage.removeItem(USER_KEY);
  }
}

/* ==========================================================================
   API Endpoint Calls
   ========================================================================== */

/**
 * Register a new user account.
 *
 * @param payload - Validated signup data (email, password, full_name).
 * @returns AuthResponse containing user details and token pair.
 */
export async function signup(payload: SignupRequest): Promise<AuthResponse> {
  return api<AuthResponse>("/auth/signup", {
    method: "POST",
    body: payload,
  });
}

/**
 * Authenticate with email and password.
 *
 * @param payload - Validated credentials.
 * @returns AuthResponse with user profile and token pair.
 */
export async function login(payload: LoginRequest): Promise<AuthResponse> {
  return api<AuthResponse>("/auth/login", {
    method: "POST",
    body: payload,
  });
}

/**
 * Refresh an expired access token using the stored refresh token.
 *
 * @param refreshToken - The active refresh token.
 * @returns TokenRefreshResponse with a fresh token pair.
 */
export async function refreshToken(token?: string): Promise<TokenRefreshResponse> {
  const payload: RefreshTokenRequest | undefined = token
    ? { refresh_token: token }
    : undefined;
  return api<TokenRefreshResponse>("/auth/refresh", {
    method: "POST",
    body: payload,
  });
}

/**
 * Fetch the current authenticated user's profile from /auth/me.
 *
 * @param accessToken - Valid Bearer access token.
 * @returns User profile entity.
 */
export async function getMe(accessToken: string): Promise<User> {
  return api<User>("/auth/me", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export type { ApiError };
