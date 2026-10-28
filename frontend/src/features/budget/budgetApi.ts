/**
 * Budget API Service.
 *
 * Typesafe calls to backend /api/events/{eventId}/budget endpoints.
 */

import { api } from "@/services/api";
import type {
  BudgetItem,
  BudgetOverviewResponse,
  CreateBudgetItemRequest,
  MessageResponse,
  UpdateBudgetItemRequest,
  WhatIfScenarioRequest,
  WhatIfScenarioResponse,
} from "@/shared/contracts";

export async function getBudgetOverview(
  eventId: string,
): Promise<BudgetOverviewResponse> {
  return api<BudgetOverviewResponse>(`/api/events/${eventId}/budget`, {
    method: "GET",
  });
}

export async function createBudgetItem(
  eventId: string,
  payload: CreateBudgetItemRequest,
): Promise<BudgetItem> {
  return api<BudgetItem>(`/api/events/${eventId}/budget`, {
    method: "POST",
    body: payload,
  });
}

export async function updateBudgetItem(
  eventId: string,
  itemId: string,
  payload: UpdateBudgetItemRequest,
): Promise<BudgetItem> {
  return api<BudgetItem>(`/api/events/${eventId}/budget/${itemId}`, {
    method: "PUT",
    body: payload,
  });
}

export async function deleteBudgetItem(
  eventId: string,
  itemId: string,
): Promise<MessageResponse> {
  return api<MessageResponse>(`/api/events/${eventId}/budget/${itemId}`, {
    method: "DELETE",
  });
}

export async function simulateWhatIfScenario(
  eventId: string,
  payload: WhatIfScenarioRequest,
): Promise<WhatIfScenarioResponse> {
  return api<WhatIfScenarioResponse>(
    `/api/events/${eventId}/what-if`,
    {
      method: "POST",
      body: payload,
    },
  );
}
