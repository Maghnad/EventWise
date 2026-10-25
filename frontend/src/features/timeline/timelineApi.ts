/**
 * Timeline API Service.
 *
 * Typesafe calls to backend /api/events/{eventId}/timeline endpoints.
 */

import { api } from "@/services/api";
import type {
  CreateTimelineTaskRequest,
  MessageResponse,
  TimelineOverviewResponse,
  TimelineTask,
  UpdateTimelineTaskRequest,
} from "@/shared/contracts";

export async function getTimelineOverview(
  eventId: string,
): Promise<TimelineOverviewResponse> {
  return api<TimelineOverviewResponse>(`/api/events/${eventId}/timeline`, {
    method: "GET",
  });
}

export async function createTimelineTask(
  eventId: string,
  payload: CreateTimelineTaskRequest,
): Promise<TimelineTask> {
  return api<TimelineTask>(`/api/events/${eventId}/timeline`, {
    method: "POST",
    body: payload,
  });
}

export async function updateTimelineTask(
  eventId: string,
  taskId: string,
  payload: UpdateTimelineTaskRequest,
): Promise<TimelineTask> {
  return api<TimelineTask>(`/api/events/${eventId}/timeline/${taskId}`, {
    method: "PATCH",
    body: payload,
  });
}

export async function deleteTimelineTask(
  eventId: string,
  taskId: string,
): Promise<MessageResponse> {
  return api<MessageResponse>(`/api/events/${eventId}/timeline/${taskId}`, {
    method: "DELETE",
  });
}
