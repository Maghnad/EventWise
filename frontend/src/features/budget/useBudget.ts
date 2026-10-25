"use client";

import { useCallback, useEffect, useState } from "react";
import type {
  BudgetItem,
  BudgetOverviewResponse,
  CreateBudgetItemRequest,
  UpdateBudgetItemRequest,
} from "@/shared/contracts";
import type { ApiError } from "@/services/api";
import * as budgetApi from "./budgetApi";

export interface UseBudgetReturn {
  overview: BudgetOverviewResponse | null;
  loading: boolean;
  error: ApiError | null;
  refetch: () => Promise<void>;
  createItem: (data: CreateBudgetItemRequest) => Promise<BudgetItem>;
  updateItem: (itemId: string, data: UpdateBudgetItemRequest) => Promise<BudgetItem>;
  deleteItem: (itemId: string) => Promise<void>;
}

export function useBudget(eventId: string): UseBudgetReturn {
  const [overview, setOverview] = useState<BudgetOverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchBudget = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await budgetApi.getBudgetOverview(eventId);
      setOverview(data);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setLoading(false);
    }
  }, [eventId]);

  useEffect(() => {
    void fetchBudget();
  }, [fetchBudget]);

  const createItem = async (data: CreateBudgetItemRequest): Promise<BudgetItem> => {
    const item = await budgetApi.createBudgetItem(eventId, data);
    await fetchBudget();
    return item;
  };

  const updateItem = async (
    itemId: string,
    data: UpdateBudgetItemRequest,
  ): Promise<BudgetItem> => {
    const item = await budgetApi.updateBudgetItem(eventId, itemId, data);
    await fetchBudget();
    return item;
  };

  const deleteItem = async (itemId: string): Promise<void> => {
    await budgetApi.deleteBudgetItem(eventId, itemId);
    await fetchBudget();
  };

  return {
    overview,
    loading,
    error,
    refetch: fetchBudget,
    createItem,
    updateItem,
    deleteItem,
  };
}
