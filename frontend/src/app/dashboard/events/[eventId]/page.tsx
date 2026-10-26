"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AuthGuard } from "@/features/auth";
import { eventsApi } from "@/features/events";
import { Card, Button } from "@/shared/components";
import type { EventDetailResponse } from "@/shared/contracts";

export default function EventDetailPage(): React.JSX.Element {
  const params = useParams<{ eventId: string }>();
  const [data, setData] = useState<EventDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!params.eventId) return;
    let mounted = true;
    setLoading(true);
    eventsApi
      .getEvent(params.eventId)
      .then((res) => {
        if (mounted) setData(res);
      })
      .catch((err) => {
        if (mounted) setError(err.message || "Failed to load event");
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [params.eventId]);

  const event = data?.event;

  return (
    <AuthGuard>
      <main className="mx-auto max-w-7xl px-6 py-16">
        <div className="mb-6">
          <Link
            href="/dashboard/events"
            className="text-xs font-medium text-indigo-400 transition-colors hover:text-indigo-300"
          >
            ← Back to All Events
          </Link>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-32">
            <div className="h-10 w-10 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
          </div>
        ) : error || !event ? (
          <Card className="mx-auto max-w-md text-center">
            <p className="text-red-400">{error || "Event not found"}</p>
            <Link href="/dashboard/events">
              <Button className="mt-4">Return to Events</Button>
            </Link>
          </Card>
        ) : (
          <section aria-labelledby="event-title">
            {/* Header */}
            <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <div className="flex items-center gap-3">
                  <h1
                    id="event-title"
                    className="text-3xl font-bold tracking-tight text-white"
                  >
                    {event.title}
                  </h1>
                  <span className="rounded-full bg-indigo-500/20 px-2.5 py-0.5 text-xs font-medium capitalize text-indigo-300">
                    {event.status}
                  </span>
                </div>
                <p className="mt-1 text-sm text-gray-400">
                  {event.description || "No description provided."}
                </p>
                <div className="mt-3 flex flex-wrap gap-4 text-xs text-gray-400">
                  <span>
                    📅 {new Date(event.start_date).toLocaleDateString()} –{" "}
                    {new Date(event.end_date).toLocaleDateString()}
                  </span>
                  <span>📍 {event.location || "Remote / TBD"}</span>
                  <span>
                    💰 {event.currency} {event.total_budget.toLocaleString()}
                  </span>
                </div>
              </div>
            </div>

            {/* Quick summary stats */}
            <div className="mb-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Card>
                <p className="text-xs font-medium uppercase tracking-wider text-gray-400">
                  Budget Spent
                </p>
                <p className="mt-2 text-2xl font-bold text-white">
                  {event.currency}{" "}
                  {data?.budget_summary?.total_spent?.toLocaleString() ?? 0}
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  of {event.currency}{" "}
                  {data?.budget_summary?.total_budget?.toLocaleString() ??
                    event.total_budget.toLocaleString()}
                </p>
              </Card>

              <Card>
                <p className="text-xs font-medium uppercase tracking-wider text-gray-400">
                  Timeline Progress
                </p>
                <p className="mt-2 text-2xl font-bold text-white">
                  {data?.timeline_summary?.completed_tasks ?? 0} /{" "}
                  {data?.timeline_summary?.total_tasks ?? 0}
                </p>
                <p className="mt-1 text-xs text-gray-500">tasks completed</p>
              </Card>

              <Card>
                <p className="text-xs font-medium uppercase tracking-wider text-gray-400">
                  Guest RSVPs
                </p>
                <p className="mt-2 text-2xl font-bold text-white">
                  {data?.guest_summary?.confirmed_guests ?? 0} confirmed
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  of {data?.guest_summary?.total_guests ?? 0} invited
                </p>
              </Card>

              <Card>
                <p className="text-xs font-medium uppercase tracking-wider text-gray-400">
                  Remaining Budget
                </p>
                <p className="mt-2 text-2xl font-bold text-white">
                  {event.currency}{" "}
                  {data?.budget_summary?.remaining_budget?.toLocaleString() ??
                    event.total_budget.toLocaleString()}
                </p>
                <p className="mt-1 text-xs text-gray-500">available funds</p>
              </Card>
            </div>

            {/* Navigation tiles to subfeatures */}
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
              <Link href={`/dashboard/events/${params.eventId}/concept`}>
                <Card className="h-full cursor-pointer transition-all hover:border-purple-500/50 hover:bg-white/[0.08]">
                  <div className="text-2xl">🎨</div>
                  <h3 className="mt-3 text-lg font-semibold text-white">
                    Concept & Moodboard
                  </h3>
                  <p className="mt-1 text-xs text-gray-400">
                    Aesthetic palettes, decor motifs, spatial flow, and GenAI visual
                    staging.
                  </p>
                  <span className="mt-4 inline-block text-xs font-medium text-purple-400">
                    Design concept →
                  </span>
                </Card>
              </Link>

              <Link href={`/dashboard/events/${params.eventId}/budget`}>
                <Card className="h-full cursor-pointer transition-all hover:border-indigo-500/50 hover:bg-white/[0.08]">
                  <div className="text-2xl">💰</div>
                  <h3 className="mt-3 text-lg font-semibold text-white">Budget</h3>
                  <p className="mt-1 text-xs text-gray-400">
                    Track itemized costs, payments, and actual expenditures.
                  </p>
                  <span className="mt-4 inline-block text-xs font-medium text-indigo-400">
                    Manage budget →
                  </span>
                </Card>
              </Link>

              <Link href={`/dashboard/events/${params.eventId}/timeline`}>
                <Card className="h-full cursor-pointer transition-all hover:border-indigo-500/50 hover:bg-white/[0.08]">
                  <div className="text-2xl">⏳</div>
                  <h3 className="mt-3 text-lg font-semibold text-white">Timeline</h3>
                  <p className="mt-1 text-xs text-gray-400">
                    Schedule milestones, deadlines, and task completions.
                  </p>
                  <span className="mt-4 inline-block text-xs font-medium text-indigo-400">
                    Manage timeline →
                  </span>
                </Card>
              </Link>

              <Link href={`/dashboard/events/${params.eventId}/vendors`}>
                <Card className="h-full cursor-pointer transition-all hover:border-indigo-500/50 hover:bg-white/[0.08]">
                  <div className="text-2xl">📋</div>
                  <h3 className="mt-3 text-lg font-semibold text-white">Vendors</h3>
                  <p className="mt-1 text-xs text-gray-400">
                    Organize supplier checklists, bookings, and deliverables.
                  </p>
                  <span className="mt-4 inline-block text-xs font-medium text-indigo-400">
                    Manage vendors →
                  </span>
                </Card>
              </Link>

              <Link href={`/dashboard/events/${params.eventId}/guests`}>
                <Card className="h-full cursor-pointer transition-all hover:border-indigo-500/50 hover:bg-white/[0.08]">
                  <div className="text-2xl">👥</div>
                  <h3 className="mt-3 text-lg font-semibold text-white">Guests</h3>
                  <p className="mt-1 text-xs text-gray-400">
                    Manage guest invitations, RSVPs, and dietary preferences.
                  </p>
                  <span className="mt-4 inline-block text-xs font-medium text-indigo-400">
                    Manage guests →
                  </span>
                </Card>
              </Link>
            </div>
          </section>
        )}
      </main>
    </AuthGuard>
  );
}
