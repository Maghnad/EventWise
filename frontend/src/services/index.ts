/** Services barrel — re-export API client and shared types. */
export { api, apiGet, apiPost, apiPut, apiPatch, apiDelete } from "./api";
export type { ApiError, ApiRequestOptions } from "./api";
export type { PaginatedResponse, BaseEntity, MessageResponse } from "./types";
