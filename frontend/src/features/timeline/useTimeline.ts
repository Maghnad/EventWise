"use client";

import { useCallback, useEffect, useState } from "react";
import type {
  CreateTimelineTaskRequest,
  TimelineOverviewResponse,
  TimelineTask,
  UpdateTimelineTaskRequest,
} from "@/shared/contracts";
import type { ApiError } from "@/services/api";
import * as timelineApi from "./timelineApi";

export interface UseTimelineReturn {
  overview: TimelineOverviewResponse | null;
  loading: boolean;
  error: ApiError | null;
  refetch: () => Promise<void>;
  createTask: (data: CreateTimelineTaskRequest) => Promise<TimelineTask>;
  updateTask: (taskId: string, data: UpdateTimelineTaskRequest) => Promise<TimelineTask>;
  deleteTask: (taskId: string) => Promise<void>;
}

export function useTimeline(eventId: string): UseTimelineReturn {
  const [overview, setOverview] = useState<TimelineOverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchTimeline = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await timelineApi.getTimelineOverview(eventId);
      setOverview(data);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setLoading(false);
    }
  }, [eventId]);

  useEffect(() => {
    void fetchTimeline();
  }, [fetchTimeline]);

  const createTask = async (data: CreateTimelineTaskRequest): Promise<TimelineTask> => {
    const task = await timelineApi.createTimelineTask(eventId, data);
    await fetchTimeline();
    return task;
  };

  const updateTask = async (
    taskId: string,
    data: UpdateTimelineTaskRequest,
  ): Promise<TimelineTask> => {
    const task = await timelineApi.updateTimelineTask(eventId, taskId, data);
    await fetchTimeline();
    return task;
  };

  const deleteTask = async (taskId: string): Promise<void> => {
    await timelineApi.deleteTimelineTask(eventId, taskId);
    await fetchTimeline();
  };

  return {
    overview,
    loading,
    error,
    refetch: fetchTimeline,
    createTask,
    updateTask,
    deleteTask,
  };
}
