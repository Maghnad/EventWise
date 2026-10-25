"use client";

import { useCallback, useEffect, useState } from "react";
import type {
  CreateEventRequest,
  Event,
  EventListParams,
  UpdateEventRequest,
} from "@/shared/contracts";
import type { ApiError } from "@/services/api";
import * as eventsApi from "./eventsApi";

export interface UseEventsReturn {
  events: Event[];
  total: number;
  loading: boolean;
  error: ApiError | null;
  refetch: () => Promise<void>;
  createEvent: (data: CreateEventRequest) => Promise<Event>;
  updateEvent: (id: string, data: UpdateEventRequest) => Promise<Event>;
  deleteEvent: (id: string) => Promise<void>;
}

export function useEvents(initialParams?: EventListParams): UseEventsReturn {
  const [events, setEvents] = useState<Event[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchEvents = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await eventsApi.getEvents(initialParams);
      setEvents(res.items);
      setTotal(res.total);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setLoading(false);
    }
  }, [initialParams]);

  useEffect(() => {
    void fetchEvents();
  }, [fetchEvents]);

  const createEvent = async (data: CreateEventRequest): Promise<Event> => {
    const created = await eventsApi.createEvent(data);
    setEvents((prev) => [created, ...prev]);
    setTotal((prev) => prev + 1);
    return created;
  };

  const updateEvent = async (id: string, data: UpdateEventRequest): Promise<Event> => {
    const updated = await eventsApi.updateEvent(id, data);
    setEvents((prev) => prev.map((e) => (e.id === id ? updated : e)));
    return updated;
  };

  const deleteEvent = async (id: string): Promise<void> => {
    await eventsApi.deleteEvent(id);
    setEvents((prev) => prev.filter((e) => e.id !== id));
    setTotal((prev) => Math.max(0, prev - 1));
  };

  return {
    events,
    total,
    loading,
    error,
    refetch: fetchEvents,
    createEvent,
    updateEvent,
    deleteEvent,
  };
}
