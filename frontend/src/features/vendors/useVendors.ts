"use client";

import { useCallback, useEffect, useState } from "react";
import type {
  CreateVendorChecklistItemRequest,
  UpdateVendorChecklistItemRequest,
  VendorChecklistItem,
  VendorChecklistResponse,
} from "@/shared/contracts";
import type { ApiError } from "@/services/api";
import * as vendorsApi from "./vendorsApi";

export interface UseVendorsReturn {
  checklist: VendorChecklistResponse | null;
  loading: boolean;
  error: ApiError | null;
  refetch: () => Promise<void>;
  createItem: (data: CreateVendorChecklistItemRequest) => Promise<VendorChecklistItem>;
  updateItem: (
    itemId: string,
    data: UpdateVendorChecklistItemRequest,
  ) => Promise<VendorChecklistItem>;
  deleteItem: (itemId: string) => Promise<void>;
}

export function useVendors(eventId: string): UseVendorsReturn {
  const [checklist, setChecklist] = useState<VendorChecklistResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchChecklist = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await vendorsApi.getVendorChecklist(eventId);
      setChecklist(data);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setLoading(false);
    }
  }, [eventId]);

  useEffect(() => {
    void fetchChecklist();
  }, [fetchChecklist]);

  const createItem = async (
    data: CreateVendorChecklistItemRequest,
  ): Promise<VendorChecklistItem> => {
    const item = await vendorsApi.createChecklistItem(eventId, data);
    await fetchChecklist();
    return item;
  };

  const updateItem = async (
    itemId: string,
    data: UpdateVendorChecklistItemRequest,
  ): Promise<VendorChecklistItem> => {
    const item = await vendorsApi.updateChecklistItem(eventId, itemId, data);
    await fetchChecklist();
    return item;
  };

  const deleteItem = async (itemId: string): Promise<void> => {
    await vendorsApi.deleteChecklistItem(eventId, itemId);
    await fetchChecklist();
  };

  return {
    checklist,
    loading,
    error,
    refetch: fetchChecklist,
    createItem,
    updateItem,
    deleteItem,
  };
}
