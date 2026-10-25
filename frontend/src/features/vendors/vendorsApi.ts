/**
 * Vendors Checklist API Service.
 *
 * Typesafe calls to backend /api/events/{eventId}/checklist endpoints.
 */

import { api } from "@/services/api";
import type {
  CreateVendorChecklistItemRequest,
  MessageResponse,
  UpdateVendorChecklistItemRequest,
  VendorChecklistItem,
  VendorChecklistResponse,
} from "@/shared/contracts";

export async function getVendorChecklist(
  eventId: string,
): Promise<VendorChecklistResponse> {
  return api<VendorChecklistResponse>(`/api/events/${eventId}/checklist`, {
    method: "GET",
  });
}

export async function createChecklistItem(
  eventId: string,
  payload: CreateVendorChecklistItemRequest,
): Promise<VendorChecklistItem> {
  return api<VendorChecklistItem>(`/api/events/${eventId}/checklist`, {
    method: "POST",
    body: payload,
  });
}

export async function updateChecklistItem(
  eventId: string,
  itemId: string,
  payload: UpdateVendorChecklistItemRequest,
): Promise<VendorChecklistItem> {
  return api<VendorChecklistItem>(`/api/events/${eventId}/checklist/${itemId}`, {
    method: "PATCH",
    body: payload,
  });
}

export async function deleteChecklistItem(
  eventId: string,
  itemId: string,
): Promise<MessageResponse> {
  return api<MessageResponse>(`/api/events/${eventId}/checklist/${itemId}`, {
    method: "DELETE",
  });
}
