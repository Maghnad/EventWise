/**
 * Centralized API client for EventWise.
 *
 * Provides a typed fetch wrapper with automatic JSON handling,
 * base URL resolution from env, and error normalisation.
 */

/* ── Types ──────────────────────────────────────────── */

/** Standard error shape returned by the backend. */
export class ApiError extends Error {
  status: number;
  detail?: unknown;

  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

/** Options passed to every request (extends native RequestInit). */
export interface ApiRequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  params?: Record<string, string>;
}

/* ── Helpers ────────────────────────────────────────── */

/**
 * Resolve the API base URL.
 *
 * Priority:
 * 1. NEXT_PUBLIC_API_BASE_URL env var (build-time, set in Vercel dashboard)
 * 2. If running in the browser on localhost → local backend
 * 3. Everything else (Vercel, custom domain, preview) → production Render URL
 */
export function getBaseUrl(): string {
  // 1. Explicit env var always wins (set in Vercel dashboard or .env.local)
  const envUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (envUrl && envUrl.trim() !== "") {
    return envUrl.trim();
  }

  // 2. Server-side (SSR / build) → production backend
  if (typeof window === "undefined") {
    return "https://eventwise.onrender.com";
  }

  // 3. Browser: only use localhost when actually developing locally
  const host = window.location.hostname;
  if (host === "localhost" || host === "127.0.0.1") {
    return "http://localhost:8000";
  }

  // 4. Any deployed host → production backend
  return "https://eventwise.onrender.com";
}

/**
 * Build a full URL from a path and optional query params.
 *
 * @param path    - API path (e.g. "/api/events")
 * @param params  - Optional query string key-value pairs
 * @returns       Fully-qualified URL string
 */
function buildUrl(path: string, params?: Record<string, string>): string {
  const url = new URL(path, getBaseUrl());
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      url.searchParams.set(key, value);
    });
  }
  return url.toString();
}

/**
 * Normalise a failed response into a consistent {@link ApiError}.
 */
async function parseError(res: Response): Promise<ApiError> {
  let detail: unknown;
  try {
    detail = await res.json();
  } catch {
    detail = await res.text();
  }
  const detailObj = detail as { detail?: string | { message?: string } } | undefined;
  let customMessage = "";
  if (detailObj && typeof detailObj.detail === "string") {
    customMessage = detailObj.detail;
  } else if (
    detailObj &&
    typeof detailObj.detail === "object" &&
    detailObj.detail?.message
  ) {
    customMessage = detailObj.detail.message;
  }
  const message = customMessage || `${res.status} ${res.statusText}`;
  return new ApiError(res.status, message, detail);
}

/* ── In-Memory Token & CSRF Storage ────────────────────────── */

let inMemoryAccessToken: string | null = null;

/** Set the active access token in memory (never written to localStorage). */
export function setAccessToken(token: string | null): void {
  inMemoryAccessToken = token;
}

/** Retrieve the current in-memory access token. */
export function getAccessToken(): string | null {
  return inMemoryAccessToken;
}

/** Read non-HttpOnly CSRF token cookie from browser document. */
function getCsrfTokenFromCookie(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(/(^|;\s*)csrf_token=([^;]+)/);
  return match ? decodeURIComponent(match[2]) : null;
}

/* ── Core fetch wrapper ─────────────────────────────── */

/**
 * Typed fetch wrapper for the EventWise API.
 *
 * @typeParam T - Expected JSON response shape
 * @param path    - API path (e.g. "/api/events")
 * @param options - Fetch options with typed body & params
 * @returns       Parsed JSON response of type T
 * @throws        {@link ApiError} on non-2xx responses
 *
 * @example
 * ```ts
 * const events = await api<Event[]>("/api/events");
 * ```
 */
export async function api<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { body, params, headers: customHeaders, ...rest } = options;

  const method = (rest.method ?? "GET").toUpperCase();
  const isMutating = ["POST", "PUT", "PATCH", "DELETE"].includes(method);
  const csrfToken = isMutating ? getCsrfTokenFromCookie() : null;

  const authHeader = inMemoryAccessToken;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...(authHeader ? { Authorization: `Bearer ${authHeader}` } : {}),
    ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
    ...customHeaders,
  };

  const targetUrl = buildUrl(path, params);
  let res: Response;
  try {
    res = await fetch(targetUrl, {
      credentials: "include",
      ...rest,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (err: unknown) {
    if (err instanceof TypeError && err.message.toLowerCase().includes("fetch")) {
      const isHttps =
        typeof window !== "undefined" && window.location.protocol === "https:";
      const isTargetHttp =
        targetUrl.startsWith("http://localhost") ||
        targetUrl.startsWith("http://127.0.0.1");
      if (isHttps && isTargetHttp) {
        throw new ApiError(
          0,
          "Backend connection failed: Your Vercel frontend (HTTPS) cannot connect to http://localhost:8000 (Mixed Content blocked by browser). Please configure NEXT_PUBLIC_API_BASE_URL in your Vercel Environment Variables to your deployed backend URL.",
        );
      }
      throw new ApiError(
        0,
        `Cannot reach backend server at ${getBaseUrl()}. Please ensure the backend is deployed and running.`,
      );
    }
    throw err;
  }

  if (!res.ok) {
    throw await parseError(res);
  }

  // 204 No Content
  if (res.status === 204) {
    return undefined as T;
  }

  return (await res.json()) as T;
}

/* ── Convenience methods ────────────────────────────── */

/** Typed GET request. */
export function apiGet<T>(path: string, params?: Record<string, string>): Promise<T> {
  return api<T>(path, { method: "GET", params });
}

/** Typed POST request. */
export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return api<T>(path, { method: "POST", body });
}

/** Typed PUT request. */
export function apiPut<T>(path: string, body?: unknown): Promise<T> {
  return api<T>(path, { method: "PUT", body });
}

/** Typed PATCH request. */
export function apiPatch<T>(path: string, body?: unknown): Promise<T> {
  return api<T>(path, { method: "PATCH", body });
}

/** Typed DELETE request. */
export function apiDelete<T = void>(path: string): Promise<T> {
  return api<T>(path, { method: "DELETE" });
}
