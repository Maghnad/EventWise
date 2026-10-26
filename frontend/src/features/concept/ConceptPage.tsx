"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { eventsApi } from "@/features/events";
import { Button, Card } from "@/shared/components";
import type { Event } from "@/shared/contracts";
import { ConceptDisplay } from "./ConceptDisplay";
import { ConceptForm } from "./ConceptForm";
import { MoodboardGallery } from "./MoodboardGallery";
import { useConcept } from "./useConcept";

export interface ConceptPageProps {
  eventId: string;
}

export function ConceptPage({ eventId }: ConceptPageProps): React.JSX.Element {
  const [event, setEvent] = useState<Event | null>(null);
  const [activeTab, setActiveTab] = useState<"concept" | "moodboard">("concept");

  const {
    concept,
    moodboard,
    loadingConcept,
    loadingMoodboard,
    error,
    fetchConcept,
    fetchMoodboard,
  } = useConcept(eventId);

  useEffect(() => {
    let mounted = true;
    eventsApi
      .getEvent(eventId)
      .then((res) => {
        if (mounted) setEvent(res.event);
      })
      .catch((err) => {
        console.error("Failed to fetch event:", err);
      });

    return () => {
      mounted = false;
    };
  }, [eventId]);

  const handleConceptSubmit = async (brief: string) => {
    const res = await fetchConcept(brief);
    if (res) {
      setActiveTab("concept");
    }
  };

  const handleGenerateMoodboard = async () => {
    if (!concept) return;
    const res = await fetchMoodboard(concept.vibe_summary);
    if (res) {
      setActiveTab("moodboard");
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      {/* Back button & Breadcrumb */}
      <div className="mb-6 flex items-center justify-between">
        <Link
          href={`/dashboard/events/${eventId}`}
          className="text-xs font-medium text-indigo-400 transition-colors hover:text-indigo-300"
        >
          ← Back to Event Overview
        </Link>
        {event && (
          <span className="rounded-full bg-white/5 px-3 py-1 text-xs text-gray-400">
            {event.title}
          </span>
        )}
      </div>

      {/* Page Header */}
      <header className="mb-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-white md:text-4xl">
              🎨 Concept & Visual Moodboard
            </h1>
            <p className="mt-2 text-sm text-gray-400">
              Translate your event vision into color palettes, styling motifs, spatial
              flow, and Generative AI visual staging prompts.
            </p>
          </div>

          {/* Tab Selector */}
          {(concept || moodboard) && (
            <div className="flex rounded-xl border border-white/10 bg-black/40 p-1 backdrop-blur-md">
              <button
                type="button"
                onClick={() => setActiveTab("concept")}
                className={`rounded-lg px-4 py-2 text-xs font-semibold transition-all ${
                  activeTab === "concept"
                    ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/25"
                    : "text-gray-400 hover:text-white"
                }`}
              >
                Concept Board {concept ? "✓" : ""}
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("moodboard")}
                className={`rounded-lg px-4 py-2 text-xs font-semibold transition-all ${
                  activeTab === "moodboard"
                    ? "bg-purple-600 text-white shadow-lg shadow-purple-500/25"
                    : "text-gray-400 hover:text-white"
                }`}
              >
                Spatial Moodboard {moodboard ? "✓" : ""}
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div
          role="alert"
          className="mb-8 flex items-center justify-between rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300"
        >
          <div className="flex items-center gap-3">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
          <Button
            variant="ghost"
            onClick={() => handleConceptSubmit("")}
            className="px-2.5 py-1 text-xs text-red-200 hover:bg-red-500/20"
          >
            Retry
          </Button>
        </div>
      )}

      {/* Main Content Layout */}
      <div className="space-y-10">
        {/* Concept Generation Form (Shown prominently when no concept exists yet) */}
        <section aria-labelledby="form-heading">
          <ConceptForm
            onSubmit={handleConceptSubmit}
            isLoading={loadingConcept}
            defaultBrief={event?.description || ""}
          />
        </section>

        {/* Tab 1: Concept Board Display */}
        {activeTab === "concept" && concept && (
          <ConceptDisplay
            concept={concept}
            onGenerateMoodboard={handleGenerateMoodboard}
            isLoadingMoodboard={loadingMoodboard}
          />
        )}

        {/* Tab 2: Moodboard & Visual Gallery */}
        {activeTab === "moodboard" && moodboard && (
          <MoodboardGallery moodboard={moodboard} />
        )}

        {/* Moodboard loading skeleton indicator */}
        {loadingMoodboard && !moodboard && (
          <Card className="flex flex-col items-center justify-center py-20 text-center">
            <div className="h-12 w-12 animate-spin rounded-full border-4 border-purple-500 border-t-transparent" />
            <p className="mt-4 text-sm font-semibold text-white">
              Staging spatial zones and generating GenAI diffusion prompts...
            </p>
            <p className="mt-1 text-xs text-gray-400">
              Allocating decor budgets across entrance, altar, tablescapes, and lounge.
            </p>
          </Card>
        )}
      </div>
    </div>
  );
}
