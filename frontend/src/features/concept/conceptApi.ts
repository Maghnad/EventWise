/**
 * Concept & Moodboard API Client.
 *
 * Interacts with AI concept generation and visual moodboard staging endpoints.
 */

import { api } from "@/services/api";
import type { AIMoodboardResponse, ConceptBoard } from "@/shared/contracts";

export interface GenerateConceptPayload {
  vibe_brief?: string;
}

export interface GenerateMoodboardPayload {
  concept?: string;
  decor_budget?: number;
}

export async function generateConcept(
  eventId: string,
  payload?: GenerateConceptPayload,
): Promise<ConceptBoard> {
  return api<ConceptBoard>(`/api/events/${eventId}/concept`, {
    method: "POST",
    body: payload || {},
  });
}

export async function generateMoodboard(
  eventId: string,
  payload?: GenerateMoodboardPayload,
): Promise<AIMoodboardResponse> {
  return api<AIMoodboardResponse>(`/api/events/${eventId}/moodboard`, {
    method: "POST",
    body: payload || {},
  });
}
