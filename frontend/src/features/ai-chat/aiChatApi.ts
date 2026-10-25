/**
 * AI Chat API Service.
 *
 * Typesafe calls to backend /api/events/{eventId}/chat endpoints.
 */

import { api } from "@/services/api";
import type {
  AIChatInputRequest,
  ChatTurnResponse,
} from "@/shared/contracts";

export async function sendChatMessage(
  eventId: string,
  payload: AIChatInputRequest,
): Promise<ChatTurnResponse> {
  return api<ChatTurnResponse>(`/api/events/${eventId}/chat`, {
    method: "POST",
    body: payload,
  });
}
