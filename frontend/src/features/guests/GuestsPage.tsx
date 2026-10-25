"use client";

import Link from "next/link";
import { useState, useCallback } from "react";
import { useGuests } from "./useGuests";
import { GuestForm } from "./GuestForm";
import { Button, Card } from "@/shared/components";
import type {
  CreateGuestRequest,
  Guest,
  GuestRsvpStatus,
  UpdateGuestRequest,
} from "@/shared/contracts";

/* ── RSVP colours ────────────────────────────────── */

const RSVP_COLORS: Record<GuestRsvpStatus, string> = {
  pending: "bg-gray-500/20 text-gray-300",
  attending: "bg-emerald-500/20 text-emerald-300",
  declined: "bg-red-500/20 text-red-300",
  tentative: "bg-amber-500/20 text-amber-300",
};

/* ── Props ───────────────────────────────────────── */

export interface GuestsPageProps {
  eventId: string;
}

export function GuestsPage({ eventId }: GuestsPageProps): React.JSX.Element {
  const { data, loading, error, refetch, createGuest, updateGuest, deleteGuest } =
    useGuests(eventId);

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Guest | undefined>();
  const [submitting, setSubmitting] = useState(false);

  const openCreate = useCallback(() => {
    setEditing(undefined);
    setFormOpen(true);
  }, []);

  const openEdit = useCallback((guest: Guest) => {
    setEditing(guest);
    setFormOpen(true);
  }, []);

  const handleSubmit = async (guestData: CreateGuestRequest) => {
    try {
      setSubmitting(true);
      if (editing) {
        await updateGuest(editing.id, guestData as UpdateGuestRequest);
      } else {
        await createGuest(guestData);
      }
      setFormOpen(false);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <Card className="mx-auto mt-16 max-w-md text-center">
        <p className="text-red-400" role="alert">
          Failed to load guests — {error?.message ?? "Unknown error"}
        </p>
        <Button className="mt-4" onClick={refetch}>
          Retry
        </Button>
      </Card>
    );
  }

  return (
    <section aria-label="Guest List">
      {/* Summary */}
      <div className="mb-8 grid gap-4 sm:grid-cols-5">
        <Card>
          <p className="text-xs uppercase tracking-wider text-gray-500">Total</p>
          <p className="mt-1 text-2xl font-bold text-white">{data.total}</p>
        </Card>
        <Card>
          <p className="text-xs uppercase tracking-wider text-gray-500">Confirmed</p>
          <p className="mt-1 text-2xl font-bold text-emerald-400">
            {data.confirmed_count}
          </p>
        </Card>
        <Card>
          <p className="text-xs uppercase tracking-wider text-gray-500">Declined</p>
          <p className="mt-1 text-2xl font-bold text-red-400">{data.declined_count}</p>
        </Card>
        <Card>
          <p className="text-xs uppercase tracking-wider text-gray-500">Pending</p>
          <p className="mt-1 text-2xl font-bold text-gray-400">{data.pending_count}</p>
        </Card>
        <Card>
          <p className="text-xs uppercase tracking-wider text-gray-500">
            Total w/ Plus Ones
          </p>
          <p className="mt-1 text-2xl font-bold text-indigo-400">
            {data.total_attending_with_plus_ones}
          </p>
        </Card>
      </div>

      {/* Header */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <h2 className="text-xl font-bold text-white">Guests</h2>
        <div className="flex items-center gap-3">
          <Link
            href={`/rsvp/${eventId}`}
            target="_blank"
            className="rounded-xl border border-indigo-500/30 bg-indigo-500/10 px-3.5 py-2 text-xs font-semibold text-indigo-300 transition-all hover:bg-indigo-500/20 hover:border-indigo-400"
            aria-label="Open public Digital RSVP page"
          >
            🔗 Public RSVP Page
          </Link>
          <Button onClick={openCreate} aria-label="Add guest">
            + Add Guest
          </Button>
        </div>
      </div>

      {/* Guest table */}
      {data.items.length === 0 ? (
        <Card className="py-16 text-center">
          <p className="mb-3 text-4xl">👥</p>
          <p className="text-gray-400">No guests yet. Add your first guest!</p>
        </Card>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-white/10">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-white/10 bg-white/5">
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-400">
                  Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-400">
                  Email
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium uppercase text-gray-400">
                  RSVP
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium uppercase text-gray-400">
                  Plus Ones
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium uppercase text-gray-400">
                  Table
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-400">
                  Dietary
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase text-gray-400">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((guest) => (
                <tr
                  key={guest.id}
                  className="border-b border-white/5 transition-colors hover:bg-white/[0.03]"
                >
                  <td className="px-4 py-3 font-medium text-white">{guest.full_name}</td>
                  <td className="px-4 py-3 text-gray-400">{guest.email}</td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium capitalize ${RSVP_COLORS[guest.rsvp_status]}`}
                    >
                      {guest.rsvp_status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center text-gray-300">
                    {guest.plus_ones}
                  </td>
                  <td className="px-4 py-3 text-center text-gray-300">
                    {guest.table_number ?? "—"}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {guest.dietary_restrictions.length > 0 ? (
                        guest.dietary_restrictions.map((d) => (
                          <span
                            key={d}
                            className="inline-block rounded-full bg-violet-500/20 px-2 py-0.5 text-[10px] text-violet-300"
                          >
                            {d}
                          </span>
                        ))
                      ) : (
                        <span className="text-gray-500">—</span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="ghost"
                        className="px-2 py-1 text-xs"
                        onClick={() => openEdit(guest)}
                        aria-label={`Edit ${guest.full_name}`}
                      >
                        Edit
                      </Button>
                      <Button
                        variant="danger"
                        className="px-2 py-1 text-xs"
                        onClick={() => deleteGuest(guest.id)}
                        aria-label={`Delete ${guest.full_name}`}
                      >
                        ✕
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <GuestForm
        isOpen={formOpen}
        onClose={() => setFormOpen(false)}
        initialData={editing}
        onSubmit={handleSubmit}
        submitting={submitting}
      />
    </section>
  );
}
