/**
 * Guests API Service.
 *
 * Typesafe calls to backend /api/events/{eventId}/guests endpoints.
 */

import { api } from "@/services/api";
import type {
  CreateGuestRequest,
  Guest,
  GuestFaqRequest,
  GuestFaqResponse,
  GuestListParams,
  GuestListResponse,
  MessageResponse,
  PublicEventResponse,
  RsvpSubmissionRequest,
  RsvpSubmissionResponse,
  UpdateGuestRequest,
} from "@/shared/contracts";

export async function getGuests(
  eventId: string,
  params?: GuestListParams,
): Promise<GuestListResponse> {
  const queryParams: Record<string, string> = {};
  if (params?.rsvp_status) queryParams.rsvp_status = params.rsvp_status;
  if (params?.search) queryParams.search = params.search;
  if (params?.page) queryParams.page = String(params.page);
  if (params?.page_size) queryParams.page_size = String(params.page_size);

  return api<GuestListResponse>(`/api/events/${eventId}/guests`, {
    method: "GET",
    params: queryParams,
  });
}

export async function createGuest(
  eventId: string,
  payload: CreateGuestRequest,
): Promise<Guest> {
  return api<Guest>(`/api/events/${eventId}/guests`, {
    method: "POST",
    body: payload,
  });
}

export async function updateGuest(
  eventId: string,
  guestId: string,
  payload: UpdateGuestRequest,
): Promise<Guest> {
  return api<Guest>(`/api/events/${eventId}/guests/${guestId}`, {
    method: "PUT",
    body: payload,
  });
}

export async function deleteGuest(
  eventId: string,
  guestId: string,
): Promise<MessageResponse> {
  return api<MessageResponse>(`/api/events/${eventId}/guests/${guestId}`, {
    method: "DELETE",
  });
}

/* ── Public Digital RSVP & FAQ endpoints (No Auth Required) ── */

export async function getPublicEvent(
  eventId: string,
): Promise<PublicEventResponse> {
  return api<PublicEventResponse>(
    `/api/events/${eventId}/public`,
    {
      method: "GET",
    },
  );
}

export async function submitPublicRsvp(
  eventId: string,
  payload: RsvpSubmissionRequest,
): Promise<RsvpSubmissionResponse> {
  return api<RsvpSubmissionResponse>(
    `/api/events/${eventId}/rsvp`,
    {
      method: "POST",
      body: payload,
    },
  );
}

export async function askGuestFaq(
  eventId: string,
  payload: GuestFaqRequest,
): Promise<GuestFaqResponse> {
  return api<GuestFaqResponse>(
    `/api/events/${eventId}/guest-faq`,
    {
      method: "POST",
      body: payload,
    },
  );
}
