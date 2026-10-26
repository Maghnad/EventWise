"use client";

import { useState, useCallback } from "react";
import { useEvents } from "./useEvents";
import { EventCard } from "./EventCard";
import { EventForm } from "./EventForm";
import { Button, Card, EmptyState, ErrorBoundary } from "@/shared/components";
import type { CreateEventRequest, Event, UpdateEventRequest } from "@/shared/contracts";

/**
 * Events listing page with CRUD modal — renders a responsive card grid.
 */
export function EventsPage(): React.JSX.Element {
  const {
    events,
    total,
    loading,
    error,
    createEvent,
    updateEvent,
    deleteEvent,
    refetch,
  } = useEvents();

  /* ── Modal state ───────────────────────────── */
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Event | undefined>();
  const [submitting, setSubmitting] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  const openCreate = useCallback(() => {
    setEditing(undefined);
    setFormOpen(true);
  }, []);

  const openEdit = useCallback((event: Event) => {
    setEditing(event);
    setFormOpen(true);
  }, []);

  const handleSubmit = async (data: CreateEventRequest) => {
    try {
      setSubmitting(true);
      if (editing) {
        await updateEvent(editing.id, data as UpdateEventRequest);
      } else {
        await createEvent(data);
      }
      setFormOpen(false);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    await deleteEvent(id);
    setDeleteConfirm(null);
  };

  /* ── Render ────────────────────────────────── */

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="mx-auto mt-16 max-w-md text-center">
        <p className="text-red-400" role="alert" aria-live="assertive">
          Failed to load events — {error.message}
        </p>
        <Button className="mt-4" onClick={refetch}>
          Retry
        </Button>
      </Card>
    );
  }

  return (
    <ErrorBoundary onReset={refetch}>
      <section aria-label="Events">
        {/* Header */}
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Events</h1>
            <p className="mt-1 text-sm text-gray-400">
              {total} event{total !== 1 && "s"} total
            </p>
          </div>
          <Button onClick={openCreate} aria-label="Create new event">
            + New Event
          </Button>
        </div>

        {/* Grid */}
        {events.length === 0 ? (
          <EmptyState
            icon="🎉"
            title="No events yet"
            description="Create your first event to start organizing timelines, itemizing budgets, and generating AI concepts."
            actionText="+ Create Your First Event"
            onAction={openCreate}
          />
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {events.map((event) => (
              <EventCard
                key={event.id}
                event={event}
                onEdit={openEdit}
                onDelete={(id) => setDeleteConfirm(id)}
              />
            ))}
          </div>
        )}

        {/* Create / Edit modal */}
        <EventForm
          isOpen={formOpen}
          onClose={() => setFormOpen(false)}
          initialData={editing}
          onSubmit={handleSubmit}
          submitting={submitting}
        />

        {/* Delete confirmation */}
        {deleteConfirm && (
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Confirm delete"
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div
              className="fixed inset-0 bg-black/70 backdrop-blur-sm"
              onClick={() => setDeleteConfirm(null)}
              aria-hidden="true"
            />
            <Card className="relative z-10 max-w-sm text-center">
              <p className="text-lg font-semibold text-white">Delete this event?</p>
              <p className="mt-2 text-sm text-gray-400">This action cannot be undone.</p>
              <div className="mt-6 flex justify-center gap-3">
                <Button variant="ghost" onClick={() => setDeleteConfirm(null)}>
                  Cancel
                </Button>
                <Button variant="danger" onClick={() => handleDelete(deleteConfirm)}>
                  Delete
                </Button>
              </div>
            </Card>
          </div>
        )}
      </section>
    </ErrorBoundary>
  );
}
