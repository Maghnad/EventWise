"use client";

import Link from "next/link";
import type { Event, EventStatus } from "@/shared/contracts";
import { Card, Button } from "@/shared/components";

/* ── Status colours ──────────────────────────────── */

const STATUS_COLORS: Record<EventStatus, string> = {
  draft: "bg-gray-500/20 text-gray-300",
  planning: "bg-blue-500/20 text-blue-300",
  confirmed: "bg-emerald-500/20 text-emerald-300",
  completed: "bg-violet-500/20 text-violet-300",
  cancelled: "bg-red-500/20 text-red-300",
};

/* ── Props ───────────────────────────────────────── */

export interface EventCardProps {
  event: Event;
  onEdit: (event: Event) => void;
  onDelete: (id: string) => void;
}

/**
 * Compact card showing key event info with edit/delete controls.
 */
export function EventCard({
  event,
  onEdit,
  onDelete,
}: EventCardProps): React.JSX.Element {
  const start = new Date(event.start_date).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
  const end = new Date(event.end_date).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  return (
    <Card className="group relative flex flex-col gap-4 transition-all hover:border-indigo-500/40 hover:bg-white/[0.07]">
      {/* Status badge */}
      <div className="flex items-center justify-between">
        <span
          className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${STATUS_COLORS[event.status]}`}
        >
          {event.status}
        </span>
        <span className="text-xs capitalize text-gray-500">{event.event_type}</span>
      </div>

      {/* Title & description */}
      <div>
        <Link href={`/dashboard/events/${event.id}`}>
          <h3 className="truncate text-lg font-semibold text-white transition-colors hover:text-indigo-300">
            {event.title}
          </h3>
        </Link>
        <p className="mt-1 line-clamp-2 text-sm text-gray-400">{event.description}</p>
      </div>

      {/* Meta grid */}
      <div className="grid grid-cols-2 gap-2 text-xs text-gray-400">
        <div>
          <span className="block text-[10px] uppercase tracking-wider text-gray-500">
            Date
          </span>
          {start} – {end}
        </div>
        <div>
          <span className="block text-[10px] uppercase tracking-wider text-gray-500">
            Location
          </span>
          <span className="block truncate">{event.location || "—"}</span>
        </div>
        <div>
          <span className="block text-[10px] uppercase tracking-wider text-gray-500">
            Budget
          </span>
          {event.currency} {event.total_budget.toLocaleString()}
        </div>
        <div>
          <span className="block text-[10px] uppercase tracking-wider text-gray-500">
            Guests
          </span>
          {event.estimated_guest_count}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2 border-t border-white/10 pt-2">
        <Link href={`/dashboard/events/${event.id}`} className="flex-1">
          <Button
            variant="primary"
            className="w-full py-1.5 text-xs"
            aria-label={`Manage event ${event.title}`}
          >
            Manage →
          </Button>
        </Link>
        <Button
          variant="secondary"
          className="py-1.5 text-xs"
          onClick={() => onEdit(event)}
          aria-label={`Edit event ${event.title}`}
        >
          Edit
        </Button>
        <Button
          variant="danger"
          className="px-3 py-1.5 text-xs"
          onClick={() => onDelete(event.id)}
          aria-label={`Delete event ${event.title}`}
        >
          Delete
        </Button>
      </div>
    </Card>
  );
}
