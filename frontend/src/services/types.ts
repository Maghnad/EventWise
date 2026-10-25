/**
 * Shared TypeScript type definitions used across features.
 */

/** Generic paginated response from the backend. */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

/** Base entity shape with UUID + timestamps. */
export interface BaseEntity {
  id: string;
  created_at: string;
  updated_at: string;
}

/** Simple message envelope returned by some endpoints. */
export interface MessageResponse {
  message: string;
}
