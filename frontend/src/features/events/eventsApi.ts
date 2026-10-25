/**
 * Events API Service.
 *
 * Typesafe calls to backend /api/events endpoints.
 */

import { api } from "@/services/api";
import type {
  CreateEventRequest,
  Event,
  EventDetailResponse,
  EventListParams,
  EventListResponse,
  MessageResponse,
  UpdateEventRequest,
} from "@/shared/contracts";

export async function getEvents(params?: EventListParams): Promise<EventListResponse> {
  const queryParams: Record<string, string> = {};
  if (params?.page) queryParams.page = String(params.page);
  if (params?.page_size) queryParams.page_size = String(params.page_size);
  if (params?.status) queryParams.status = params.status;
  if (params?.search) queryParams.search = params.search;

  return api<EventListResponse>("/api/events", {
    method: "GET",
    params: queryParams,
  });
}

export async function getEvent(id: string): Promise<EventDetailResponse> {
  return api<EventDetailResponse>(`/api/events/${id}`, {
    method: "GET",
  });
}

export async function createEvent(payload: CreateEventRequest): Promise<Event> {
  return api<Event>("/api/events", {
    method: "POST",
    body: payload,
  });
}

export async function updateEvent(
  id: string,
  payload: UpdateEventRequest,
): Promise<Event> {
  return api<Event>(`/api/events/${id}`, {
    method: "PUT",
    body: payload,
  });
}

export async function deleteEvent(id: string): Promise<MessageResponse> {
  return api<MessageResponse>(`/api/events/${id}`, {
    method: "DELETE",
  });
}
