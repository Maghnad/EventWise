"use client";

import { useCallback, useEffect, useState } from "react";
import type {
  CreateGuestRequest,
  Guest,
  GuestListParams,
  GuestListResponse,
  UpdateGuestRequest,
} from "@/shared/contracts";
import type { ApiError } from "@/services/api";
import * as guestsApi from "./guestsApi";

export interface UseGuestsReturn {
  data: GuestListResponse | null;
  loading: boolean;
  error: ApiError | null;
  refetch: () => Promise<void>;
  createGuest: (data: CreateGuestRequest) => Promise<Guest>;
  updateGuest: (guestId: string, data: UpdateGuestRequest) => Promise<Guest>;
  deleteGuest: (guestId: string) => Promise<void>;
}

export function useGuests(eventId: string, params?: GuestListParams): UseGuestsReturn {
  const [data, setData] = useState<GuestListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchGuests = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await guestsApi.getGuests(eventId, params);
      setData(res);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setLoading(false);
    }
  }, [eventId, params]);

  useEffect(() => {
    void fetchGuests();
  }, [fetchGuests]);

  const createGuest = async (guestData: CreateGuestRequest): Promise<Guest> => {
    const guest = await guestsApi.createGuest(eventId, guestData);
    await fetchGuests();
    return guest;
  };

  const updateGuest = async (
    guestId: string,
    guestData: UpdateGuestRequest,
  ): Promise<Guest> => {
    const guest = await guestsApi.updateGuest(eventId, guestId, guestData);
    await fetchGuests();
    return guest;
  };

  const deleteGuest = async (guestId: string): Promise<void> => {
    await guestsApi.deleteGuest(eventId, guestId);
    await fetchGuests();
  };

  return {
    data,
    loading,
    error,
    refetch: fetchGuests,
    createGuest,
    updateGuest,
    deleteGuest,
  };
}
