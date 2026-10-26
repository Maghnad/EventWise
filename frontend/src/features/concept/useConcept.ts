"use client";

import { useCallback, useState } from "react";
import type { AIMoodboardResponse, ConceptBoard } from "@/shared/contracts";
import { generateConcept, generateMoodboard } from "./conceptApi";

export interface UseConceptReturn {
  concept: ConceptBoard | null;
  moodboard: AIMoodboardResponse | null;
  loadingConcept: boolean;
  loadingMoodboard: boolean;
  error: string | null;
  fetchConcept: (vibeBrief?: string) => Promise<ConceptBoard | null>;
  fetchMoodboard: (
    conceptSummary?: string,
    decorBudget?: number,
  ) => Promise<AIMoodboardResponse | null>;
  reset: () => void;
}

export function useConcept(eventId: string): UseConceptReturn {
  const [concept, setConcept] = useState<ConceptBoard | null>(null);
  const [moodboard, setMoodboard] = useState<AIMoodboardResponse | null>(null);
  const [loadingConcept, setLoadingConcept] = useState(false);
  const [loadingMoodboard, setLoadingMoodboard] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchConcept = useCallback(
    async (vibeBrief?: string): Promise<ConceptBoard | null> => {
      if (!eventId) return null;
      setLoadingConcept(true);
      setError(null);
      try {
        const res = await generateConcept(eventId, { vibe_brief: vibeBrief });
        setConcept(res);
        return res;
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Failed to generate concept";
        setError(message);
        return null;
      } finally {
        setLoadingConcept(false);
      }
    },
    [eventId],
  );

  const fetchMoodboard = useCallback(
    async (
      conceptSummary?: string,
      decorBudget?: number,
    ): Promise<AIMoodboardResponse | null> => {
      if (!eventId) return null;
      setLoadingMoodboard(true);
      setError(null);
      try {
        const res = await generateMoodboard(eventId, {
          concept: conceptSummary,
          decor_budget: decorBudget,
        });
        setMoodboard(res);
        return res;
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : "Failed to generate moodboard";
        setError(message);
        return null;
      } finally {
        setLoadingMoodboard(false);
      }
    },
    [eventId],
  );

  const reset = useCallback(() => {
    setConcept(null);
    setMoodboard(null);
    setError(null);
  }, []);

  return {
    concept,
    moodboard,
    loadingConcept,
    loadingMoodboard,
    error,
    fetchConcept,
    fetchMoodboard,
    reset,
  };
}
