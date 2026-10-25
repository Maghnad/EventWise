"use client";

import { useEffect, useState, useCallback } from "react";
import type { ApiError } from "@/services/api";

/**
 * State shape returned by {@link useAsync}.
 */
interface AsyncState<T> {
  data: T | null;
  error: ApiError | null;
  loading: boolean;
  refetch: () => void;
}

/**
 * Generic hook for async data fetching with loading/error states.
 *
 * @param fetcher - Async function returning data of type T
 * @returns       Object with data, error, loading, and refetch
 *
 * @example
 * ```ts
 * const { data, loading } = useAsync(() => apiGet<Event[]>("/api/events"));
 * ```
 */
export function useAsync<T>(fetcher: () => Promise<T>): AsyncState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [trigger, setTrigger] = useState<number>(0);

  const refetch = useCallback(() => setTrigger((t) => t + 1), []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    fetcher()
      .then((result) => {
        if (!cancelled) {
          setData(result);
          setError(null);
        }
      })
      .catch((err: ApiError) => {
        if (!cancelled) {
          setError(err);
          setData(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trigger]);

  return { data, error, loading, refetch };
}
