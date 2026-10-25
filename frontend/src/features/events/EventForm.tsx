"use client";

import { useState, useCallback, type FormEvent } from "react";
import { z } from "zod";
import { Input, Button, Modal } from "@/shared/components";
import type {
  CreateEventRequest,
  Event,
  EventType,
  EventStatus,
} from "@/shared/contracts";

/* ── Zod Schema ──────────────────────────────────── */

export const eventFormSchema = z.object({
  title: z.string().min(1, "Title is required").max(200),
  description: z.string().max(2000).optional().default(""),
  event_type: z.enum([
    "wedding",
    "conference",
    "birthday",
    "corporate",
    "social",
    "workshop",
    "other",
  ] as const),
  location: z.string().max(500).optional().default(""),
  start_date: z.string().min(1, "Start date is required"),
  end_date: z.string().min(1, "End date is required"),
  estimated_guest_count: z.coerce.number().int().min(0).default(0),
  total_budget: z.coerce.number().min(0).default(0),
  currency: z.string().min(1).max(3).default("USD"),
  status: z
    .enum(["draft", "planning", "confirmed", "completed", "cancelled"] as const)
    .default("draft"),
});

export type EventFormValues = z.infer<typeof eventFormSchema>;

/* ── Defaults ────────────────────────────────────── */

const EMPTY: EventFormValues = {
  title: "",
  description: "",
  event_type: "other",
  location: "",
  start_date: "",
  end_date: "",
  estimated_guest_count: 0,
  total_budget: 0,
  currency: "USD",
  status: "draft",
};

const EVENT_TYPES: EventType[] = [
  "wedding",
  "conference",
  "birthday",
  "corporate",
  "social",
  "workshop",
  "other",
];
const EVENT_STATUSES: EventStatus[] = [
  "draft",
  "planning",
  "confirmed",
  "completed",
  "cancelled",
];

/* ── Props ───────────────────────────────────────── */

export interface EventFormProps {
  isOpen: boolean;
  onClose: () => void;
  /** If provided, form is in edit mode. */
  initialData?: Event;
  onSubmit: (data: CreateEventRequest) => Promise<void>;
  submitting?: boolean;
}

/**
 * Modal form for creating / editing events with Zod validation.
 */
export function EventForm({
  isOpen,
  onClose,
  initialData,
  onSubmit,
  submitting = false,
}: EventFormProps): React.JSX.Element {
  const isEdit = Boolean(initialData);

  const defaults: EventFormValues = initialData
    ? {
        title: initialData.title,
        description: initialData.description,
        event_type: initialData.event_type,
        location: initialData.location,
        start_date: initialData.start_date.slice(0, 16),
        end_date: initialData.end_date.slice(0, 16),
        estimated_guest_count: initialData.estimated_guest_count,
        total_budget: initialData.total_budget,
        currency: initialData.currency,
        status: initialData.status,
      }
    : EMPTY;

  const [values, setValues] = useState<EventFormValues>(defaults);
  const [errors, setErrors] = useState<Partial<Record<keyof EventFormValues, string>>>(
    {},
  );

  const setValue = useCallback(
    <K extends keyof EventFormValues>(key: K, value: EventFormValues[K]) => {
      setValues((prev) => ({ ...prev, [key]: value }));
      setErrors((prev) => ({ ...prev, [key]: undefined }));
    },
    [],
  );

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const result = eventFormSchema.safeParse(values);
    if (!result.success) {
      const fieldErrors: Partial<Record<keyof EventFormValues, string>> = {};
      result.error.issues.forEach((err) => {
        const field = err.path[0] as keyof EventFormValues;
        if (!fieldErrors[field]) fieldErrors[field] = err.message;
      });
      setErrors(fieldErrors);
      return;
    }
    await onSubmit(result.data as CreateEventRequest);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEdit ? "Edit Event" : "Create Event"}
      description="Fill in the event details below."
      className="max-w-2xl"
    >
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input
            label="Title"
            placeholder="Event title"
            value={values.title}
            onChange={(e) => setValue("title", e.target.value)}
            error={errors.title}
            required
          />

          <div className="w-full">
            <label
              htmlFor="event_type"
              className="mb-1.5 block text-xs font-medium text-gray-300"
            >
              Type
            </label>
            <select
              id="event_type"
              value={values.event_type}
              onChange={(e) => setValue("event_type", e.target.value as EventType)}
              className="w-full rounded-lg border border-white/20 bg-white/5 px-3.5 py-2 text-sm text-white backdrop-blur-md transition-colors focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              {EVENT_TYPES.map((t) => (
                <option key={t} value={t} className="bg-gray-900">
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </option>
              ))}
            </select>
          </div>
        </div>

        <Input
          label="Description"
          placeholder="Brief event description"
          value={values.description}
          onChange={(e) => setValue("description", e.target.value)}
          error={errors.description}
        />

        <Input
          label="Location"
          placeholder="Venue / address"
          value={values.location}
          onChange={(e) => setValue("location", e.target.value)}
          error={errors.location}
        />

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input
            label="Start Date"
            type="datetime-local"
            value={values.start_date}
            onChange={(e) => setValue("start_date", e.target.value)}
            error={errors.start_date}
            required
          />
          <Input
            label="End Date"
            type="datetime-local"
            value={values.end_date}
            onChange={(e) => setValue("end_date", e.target.value)}
            error={errors.end_date}
            required
          />
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <Input
            label="Guest Count"
            type="number"
            min={0}
            value={String(values.estimated_guest_count)}
            onChange={(e) => setValue("estimated_guest_count", Number(e.target.value))}
            error={errors.estimated_guest_count}
          />
          <Input
            label="Total Budget"
            type="number"
            min={0}
            step={0.01}
            value={String(values.total_budget)}
            onChange={(e) => setValue("total_budget", Number(e.target.value))}
            error={errors.total_budget}
          />
          <Input
            label="Currency"
            maxLength={3}
            value={values.currency}
            onChange={(e) => setValue("currency", e.target.value.toUpperCase())}
            error={errors.currency}
          />
        </div>

        <div className="w-full">
          <label
            htmlFor="status"
            className="mb-1.5 block text-xs font-medium text-gray-300"
          >
            Status
          </label>
          <select
            id="status"
            value={values.status}
            onChange={(e) => setValue("status", e.target.value as EventStatus)}
            className="w-full rounded-lg border border-white/20 bg-white/5 px-3.5 py-2 text-sm text-white backdrop-blur-md transition-colors focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            {EVENT_STATUSES.map((s) => (
              <option key={s} value={s} className="bg-gray-900">
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {/* Submit */}
        <div className="flex justify-end gap-3 border-t border-white/10 pt-4">
          <Button variant="ghost" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting ? "Saving…" : isEdit ? "Update" : "Create"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
