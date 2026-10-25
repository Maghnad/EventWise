"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import React, { useEffect, useMemo, useState } from "react";
import { AuthGuard } from "@/features/auth";
import { eventsApi, useEvents } from "@/features/events";
import { getVendorChecklist } from "@/features/vendors/vendorsApi";
import { Button, Card, EmptyState, ErrorBoundary, Modal } from "@/shared/components";
import type { Event, EventDetailResponse } from "@/shared/contracts";

interface FeatureCardConfig {
  title: string;
  description: string;
  icon: string;
  tag: string;
  href?: string;
  moduleKey?: "budget" | "timeline" | "vendors" | "guests" | "concept";
}

interface EventProgressMetrics {
  budgetSpent: number;
  totalBudget: number;
  budgetPct: number;
  timelineDone: number;
  timelineTotal: number;
  timelinePct: number;
  checklistDone: number;
  checklistTotal: number;
  checklistPct: number;
}

const SECTIONS: FeatureCardConfig[] = [
  {
    title: "Events",
    description: "Create, view, and organize all your upcoming events.",
    icon: "🎉",
    tag: "Core",
    href: "/dashboard/events",
  },
  {
    title: "Budget",
    description: "Track itemized expenses, payments, and simulate what-if scenarios.",
    icon: "💰",
    tag: "Finance",
    moduleKey: "budget",
  },
  {
    title: "Timeline",
    description: "Orchestrate production schedules, deadlines, and milestone tasks.",
    icon: "📅",
    tag: "Schedule",
    moduleKey: "timeline",
  },
  {
    title: "Vendors",
    description: "Manage vendor categories, checklist deliverables, and quotes.",
    icon: "🤝",
    tag: "Operations",
    moduleKey: "vendors",
  },
  {
    title: "Guests & RSVP",
    description: "Headcount tracking, dietary restrictions, and public digital RSVP.",
    icon: "👥",
    tag: "Attendance",
    moduleKey: "guests",
  },
  {
    title: "AI Chat & Concepts",
    description: "Converse with AI planner, generate color palettes and moodboards.",
    icon: "✨",
    tag: "Intelligence",
    href: "/dashboard/ai-chat",
  },
];

export default function DashboardPage(): React.JSX.Element {
  const router = useRouter();
  const { events, total, loading, error, refetch } = useEvents();

  // Progress metrics map keyed by event id
  const [metricsMap, setMetricsMap] = useState<Record<string, EventProgressMetrics>>({});

  // Search and filter state
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  // Module selector modal
  const [selectedModule, setSelectedModule] = useState<{
    key: "budget" | "timeline" | "vendors" | "guests" | "concept";
    title: string;
  } | null>(null);

  // Fetch detailed metrics for all visible events
  useEffect(() => {
    let isCancelled = false;

    async function loadAllMetrics() {
      if (!events || events.length === 0) return;

      const newMetrics: Record<string, EventProgressMetrics> = {};

      await Promise.all(
        events.map(async (evt) => {
          try {
            // Fetch event detail (budget + timeline summaries)
            const detail: EventDetailResponse = await eventsApi.getEvent(evt.id);

            // Fetch vendor checklist
            let checklistDone = 0;
            let checklistTotal = 0;
            let checklistPct = 0;

            try {
              const checklist = await getVendorChecklist(evt.id);
              checklistDone = checklist.completed_items;
              checklistTotal = checklist.total_items;
              checklistPct =
                checklist.total_items > 0
                  ? Math.min(100, Math.round((checklist.completed_items / checklist.total_items) * 100))
                  : 0;
            } catch {
              // Checklist fallback
            }

            const budgetSpent = Number(detail.budget_summary?.total_spent ?? 0);
            const totalBudget = Number(detail.budget_summary?.total_budget ?? evt.total_budget ?? 0);
            const budgetPct = totalBudget > 0 ? Math.min(100, Math.round((budgetSpent / totalBudget) * 100)) : 0;

            const timelineDone = detail.timeline_summary?.completed_tasks ?? 0;
            const timelineTotal = detail.timeline_summary?.total_tasks ?? 0;
            const timelinePct = timelineTotal > 0 ? Math.min(100, Math.round((timelineDone / timelineTotal) * 100)) : 0;

            newMetrics[evt.id] = {
              budgetSpent,
              totalBudget,
              budgetPct,
              timelineDone,
              timelineTotal,
              timelinePct,
              checklistDone,
              checklistTotal,
              checklistPct,
            };
          } catch {
            // Fallback metrics if event detail call fails
            newMetrics[evt.id] = {
              budgetSpent: 0,
              totalBudget: Number(evt.total_budget || 0),
              budgetPct: 0,
              timelineDone: 0,
              timelineTotal: 0,
              timelinePct: 0,
              checklistDone: 0,
              checklistTotal: 0,
              checklistPct: 0,
            };
          }
        }),
      );

      if (!isCancelled) {
        setMetricsMap(newMetrics);
      }
    }

    loadAllMetrics();

    return () => {
      isCancelled = true;
    };
  }, [events]);

  // Filtered events
  const filteredEvents = useMemo(() => {
    return events.filter((evt) => {
      const matchesSearch =
        evt.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (evt.location && evt.location.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (evt.description && evt.description.toLowerCase().includes(searchQuery.toLowerCase()));

      const matchesStatus =
        statusFilter === "all" || evt.status.toLowerCase() === statusFilter.toLowerCase();

      return matchesSearch && matchesStatus;
    });
  }, [events, searchQuery, statusFilter]);

  // Aggregated totals
  const aggregateStats = useMemo(() => {
    let totalBudgetSum = 0;
    let totalSpentSum = 0;

    for (const evt of events) {
      totalBudgetSum += Number(evt.total_budget || 0);
      const m = metricsMap[evt.id];
      if (m) {
        totalSpentSum += m.budgetSpent;
      }
    }

    return {
      totalEvents: events.length,
      totalBudgetSum,
      totalSpentSum,
    };
  }, [events, metricsMap]);

  const handleCardClick = (section: FeatureCardConfig) => {
    if (section.href) {
      router.push(section.href);
      return;
    }

    if (section.moduleKey) {
      if (events.length === 0) {
        router.push("/dashboard/events");
        return;
      }

      if (events.length === 1) {
        router.push(`/dashboard/events/${events[0].id}/${section.moduleKey}`);
        return;
      }

      setSelectedModule({ key: section.moduleKey, title: section.title });
    }
  };

  const handleSelectEventForModule = (event: Event) => {
    if (!selectedModule) return;
    const target = `/dashboard/events/${event.id}/${selectedModule.key}`;
    setSelectedModule(null);
    router.push(target);
  };

  return (
    <AuthGuard>
      <ErrorBoundary onReset={refetch}>
        <main
          aria-label="EventWise Main Dashboard"
          className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-10 sm:py-16 space-y-12"
        >
          {/* Header */}
          <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-white/10 pb-8">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-indigo-400/20 bg-indigo-500/10 px-3 py-1 text-xs font-semibold text-indigo-300 mb-2">
                <span>⚡</span>
                <span>Command Center</span>
              </div>
              <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
                Event Dashboard
              </h1>
              <p className="mt-1 text-sm text-gray-400">
                Live visibility across event budgets, milestone timelines, and vendor deliverables.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Link href="/dashboard/events">
                <Button variant="primary" className="shadow-lg shadow-indigo-600/30">
                  + Create Event
                </Button>
              </Link>
            </div>
          </header>

          {/* Quick Stats Overview */}
          <section aria-label="Key Aggregate Metrics" className="grid gap-4 sm:grid-cols-3">
            <Card className="rounded-2xl border-white/10 bg-white/[0.02] p-5">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-400">
                Total Managed Events
              </span>
              <p className="mt-2 text-3xl font-extrabold text-white">
                {loading ? "..." : aggregateStats.totalEvents}
              </p>
              <p className="mt-1 text-xs text-indigo-400 font-medium">
                {total} recorded in workspace
              </p>
            </Card>

            <Card className="rounded-2xl border-white/10 bg-white/[0.02] p-5">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-400">
                Total Budget Allocated
              </span>
              <p className="mt-2 text-3xl font-extrabold text-blue-400">
                ${aggregateStats.totalBudgetSum.toLocaleString()}
              </p>
              <p className="mt-1 text-xs text-gray-500">
                Across all active planning files
              </p>
            </Card>

            <Card className="rounded-2xl border-white/10 bg-white/[0.02] p-5">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-400">
                Total Expenses Logged
              </span>
              <p className="mt-2 text-3xl font-extrabold text-emerald-400">
                ${aggregateStats.totalSpentSum.toLocaleString()}
              </p>
              <p className="mt-1 text-xs text-gray-500">
                {aggregateStats.totalBudgetSum > 0
                  ? `${Math.round((aggregateStats.totalSpentSum / aggregateStats.totalBudgetSum) * 100)}% portfolio utilization`
                  : "No budget data"}
              </p>
            </Card>
          </section>

          {/* Feature Modules Navigation Grid */}
          <section aria-label="Feature modules">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span>🚀</span>
                <span>Planning Modules</span>
              </h2>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {SECTIONS.map((section) => (
                <Card
                  key={section.title}
                  onClick={() => handleCardClick(section)}
                  className="group relative cursor-pointer border border-white/10 bg-white/[0.03] p-5 transition-all duration-200 hover:-translate-y-1 hover:border-indigo-500/50 hover:bg-white/[0.06] hover:shadow-xl hover:shadow-indigo-500/10 rounded-2xl"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-3xl" role="img" aria-label={section.title}>
                      {section.icon}
                    </span>
                    <span className="rounded-full border border-indigo-500/20 bg-indigo-500/10 px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-indigo-300">
                      {section.tag}
                    </span>
                  </div>
                  <h3 className="mt-3 text-base font-bold text-white transition-colors group-hover:text-indigo-300">
                    {section.title}
                  </h3>
                  <p className="mt-1 text-xs text-gray-400 leading-relaxed">
                    {section.description}
                  </p>
                  <div className="mt-4 flex items-center text-xs font-semibold text-indigo-400 group-hover:text-indigo-300">
                    <span>Explore {section.title}</span>
                    <span className="ml-1.5 transition-transform group-hover:translate-x-1">→</span>
                  </div>
                </Card>
              ))}
            </div>
          </section>

          {/* All Events with Live Progress Bars */}
          <section aria-labelledby="all-events-heading" className="space-y-6 pt-4">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 id="all-events-heading" className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                  <span>📊</span>
                  <span>Event Progress Overview</span>
                </h2>
                <p className="text-xs text-gray-400 mt-1">
                  Real-time budget spend, timeline task completion, and vendor checklist metrics.
                </p>
              </div>

              {/* Search and Status Filters */}
              <div className="flex flex-wrap items-center gap-3">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Filter events by name or venue..."
                  className="rounded-xl border border-white/10 bg-white/[0.04] px-3.5 py-2 text-xs text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none w-56 sm:w-64"
                  aria-label="Filter events search"
                />

                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="rounded-xl border border-white/10 bg-black/60 px-3 py-2 text-xs text-gray-300 focus:border-indigo-500 focus:outline-none"
                  aria-label="Filter events by status"
                >
                  <option value="all">All Statuses</option>
                  <option value="draft">Draft</option>
                  <option value="planning">Planning</option>
                  <option value="confirmed">Confirmed</option>
                  <option value="completed">Completed</option>
                </select>
              </div>
            </div>

            {/* Loading State */}
            {loading ? (
              <div className="flex flex-col items-center justify-center py-20 space-y-3">
                <div className="h-10 w-10 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
                <p className="text-xs text-gray-400 font-medium">Loading event progress data...</p>
              </div>
            ) : error ? (
              /* Error State */
              <Card className="rounded-2xl border-red-500/30 bg-red-500/10 p-8 text-center max-w-md mx-auto">
                <p className="text-3xl mb-2">⚠️</p>
                <h3 className="text-base font-bold text-white">Failed to load events</h3>
                <p className="mt-1 text-xs text-red-300">{error.message}</p>
                <Button className="mt-4 text-xs" onClick={refetch}>
                  Retry
                </Button>
              </Card>
            ) : filteredEvents.length === 0 ? (
              /* Empty State */
              <EmptyState
                icon="🎉"
                title={events.length === 0 ? "No events created yet" : "No matching events found"}
                description={
                  events.length === 0
                    ? "Get started by creating your first event to unlock live progress tracking, budget analysis, and AI planning."
                    : "Try adjusting your search query or status filter to find the event you are looking for."
                }
                actionText={events.length === 0 ? "+ Create First Event" : undefined}
                actionHref={events.length === 0 ? "/dashboard/events" : undefined}
                secondaryActionText={events.length > 0 ? "Clear Filters" : undefined}
                secondaryActionHref={events.length > 0 ? "#" : undefined}
                onAction={() => {
                  setSearchQuery("");
                  setStatusFilter("all");
                }}
              />
            ) : (
              /* Event Cards Grid with Progress Bars */
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {filteredEvents.map((event) => {
                  const m = metricsMap[event.id] || {
                    budgetSpent: 0,
                    totalBudget: Number(event.total_budget || 0),
                    budgetPct: 0,
                    timelineDone: 0,
                    timelineTotal: 0,
                    timelinePct: 0,
                    checklistDone: 0,
                    checklistTotal: 0,
                    checklistPct: 0,
                  };

                  return (
                    <Card
                      key={event.id}
                      className="flex flex-col justify-between rounded-3xl border border-white/10 bg-gradient-to-b from-white/[0.04] via-black/40 to-black/70 p-6 shadow-xl transition-all hover:border-indigo-500/40 hover:shadow-2xl hover:shadow-indigo-500/5 backdrop-blur-xl"
                    >
                      {/* Event Header info */}
                      <div>
                        <div className="flex items-center justify-between gap-2 mb-3">
                          <span
                            className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                              event.status === "completed"
                                ? "bg-emerald-500/20 text-emerald-300"
                                : event.status === "confirmed"
                                ? "bg-blue-500/20 text-blue-300"
                                : "bg-purple-500/20 text-purple-300"
                            }`}
                          >
                            {event.status}
                          </span>

                          <span className="text-[11px] font-semibold text-gray-400">
                            {event.event_type}
                          </span>
                        </div>

                        <Link href={`/dashboard/events/${event.id}`}>
                          <h3 className="text-lg font-bold text-white transition-colors hover:text-indigo-300 truncate">
                            {event.title}
                          </h3>
                        </Link>

                        <div className="mt-1.5 flex items-center gap-2 text-xs text-gray-400">
                          <span>📍 {event.location || "Venue TBD"}</span>
                          <span>•</span>
                          <span>
                            {event.start_date
                              ? new Date(event.start_date).toLocaleDateString([], {
                                  month: "short",
                                  day: "numeric",
                                })
                              : "Date TBD"}
                          </span>
                        </div>
                      </div>

                      {/* 3 Progress Bars: Budget, Timeline, Checklist */}
                      <div className="my-6 space-y-4 rounded-2xl border border-white/5 bg-black/40 p-4">
                        {/* 1. Budget Spent Progress */}
                        <div>
                          <div className="flex items-center justify-between text-xs mb-1.5">
                            <span className="font-semibold text-gray-300 flex items-center gap-1.5">
                              <span>💰</span>
                              <span>Budget Spent</span>
                            </span>
                            <span className="font-mono text-gray-400 font-medium">
                              ${m.budgetSpent.toLocaleString()} / ${m.totalBudget.toLocaleString()}{" "}
                              <strong className={m.budgetPct > 90 ? "text-red-400" : m.budgetPct > 70 ? "text-amber-400" : "text-emerald-400"}>
                                ({m.budgetPct}%)
                              </strong>
                            </span>
                          </div>
                          <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
                            <div
                              className={`h-full rounded-full transition-all duration-500 ${
                                m.budgetPct > 90
                                  ? "bg-red-500"
                                  : m.budgetPct > 70
                                  ? "bg-amber-500"
                                  : "bg-emerald-500"
                              }`}
                              style={{ width: `${Math.min(m.budgetPct, 100)}%` }}
                            />
                          </div>
                        </div>

                        {/* 2. Timeline Completion Progress */}
                        <div>
                          <div className="flex items-center justify-between text-xs mb-1.5">
                            <span className="font-semibold text-gray-300 flex items-center gap-1.5">
                              <span>⏳</span>
                              <span>Timeline Tasks</span>
                            </span>
                            <span className="font-mono text-gray-400 font-medium">
                              {m.timelineDone} / {m.timelineTotal} done{" "}
                              <strong className="text-indigo-400">({m.timelinePct}%)</strong>
                            </span>
                          </div>
                          <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
                            <div
                              className="h-full rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-all duration-500"
                              style={{ width: `${Math.min(m.timelinePct, 100)}%` }}
                            />
                          </div>
                        </div>

                        {/* 3. Vendor Checklist Progress */}
                        <div>
                          <div className="flex items-center justify-between text-xs mb-1.5">
                            <span className="font-semibold text-gray-300 flex items-center gap-1.5">
                              <span>✅</span>
                              <span>Checklist Done</span>
                            </span>
                            <span className="font-mono text-gray-400 font-medium">
                              {m.checklistDone} / {m.checklistTotal} done{" "}
                              <strong className="text-purple-400">({m.checklistPct}%)</strong>
                            </span>
                          </div>
                          <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
                            <div
                              className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-500"
                              style={{ width: `${Math.min(m.checklistPct, 100)}%` }}
                            />
                          </div>
                        </div>
                      </div>

                      {/* Footer Action Badges */}
                      <div className="grid grid-cols-5 gap-1 border-t border-white/10 pt-3 text-center text-[10px] font-semibold text-gray-300">
                        <Link
                          href={`/dashboard/events/${event.id}/budget`}
                          className="rounded-lg p-1.5 hover:bg-white/10 hover:text-white transition-colors"
                          title="Budget"
                        >
                          💰 Budget
                        </Link>
                        <Link
                          href={`/dashboard/events/${event.id}/timeline`}
                          className="rounded-lg p-1.5 hover:bg-white/10 hover:text-white transition-colors"
                          title="Timeline"
                        >
                          ⏳ Sched
                        </Link>
                        <Link
                          href={`/dashboard/events/${event.id}/vendors`}
                          className="rounded-lg p-1.5 hover:bg-white/10 hover:text-white transition-colors"
                          title="Vendors"
                        >
                          🤝 Vendors
                        </Link>
                        <Link
                          href={`/dashboard/events/${event.id}/concept`}
                          className="rounded-lg p-1.5 hover:bg-white/10 hover:text-white transition-colors"
                          title="Concept & Moodboard"
                        >
                          🎨 Vibe
                        </Link>
                        <Link
                          href={`/rsvp/${event.id}`}
                          target="_blank"
                          className="rounded-lg p-1.5 text-indigo-400 hover:bg-indigo-500/20 hover:text-indigo-200 transition-colors"
                          title="Digital RSVP Page"
                        >
                          🔗 RSVP
                        </Link>
                      </div>
                    </Card>
                  );
                })}
              </div>
            )}
          </section>

          {/* Module Selector Modal */}
          <Modal
            isOpen={selectedModule !== null}
            onClose={() => setSelectedModule(null)}
            title={`Select Event for ${selectedModule?.title ?? "Module"}`}
          >
            <div className="space-y-3 py-2">
              <p className="text-xs text-gray-400">
                Choose which event you would like to open {selectedModule?.title} for:
              </p>
              <div className="max-h-64 space-y-2 overflow-y-auto pr-1">
                {events.map((evt) => (
                  <button
                    key={evt.id}
                    type="button"
                    onClick={() => handleSelectEventForModule(evt)}
                    className="flex w-full items-center justify-between rounded-xl border border-white/10 bg-white/5 p-3 text-left transition-all hover:border-indigo-500/50 hover:bg-indigo-500/10"
                  >
                    <div>
                      <p className="text-sm font-semibold text-white">{evt.title}</p>
                      <p className="text-xs text-gray-400">
                        {evt.start_date ? new Date(evt.start_date).toLocaleDateString() : "Date TBD"} ·{" "}
                        {evt.location || "Location TBD"}
                      </p>
                    </div>
                    <span className="text-xs font-semibold text-indigo-400">Select →</span>
                  </button>
                ))}
              </div>
            </div>
          </Modal>
        </main>
      </ErrorBoundary>
    </AuthGuard>
  );
}
