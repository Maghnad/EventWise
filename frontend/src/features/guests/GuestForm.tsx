"use client";

import { useState, type FormEvent } from "react";
import { z } from "zod";
import { Input, Button, Modal } from "@/shared/components";
import type { CreateGuestRequest, Guest, GuestRsvpStatus } from "@/shared/contracts";

/* ── Zod Schema ──────────────────────────────────── */

export const guestFormSchema = z.object({
  full_name: z.string().min(1, "Name is required").max(200),
  email: z.string().email("Valid email is required"),
  phone: z.string().nullable().optional().default(null),
  rsvp_status: z
    .enum(["pending", "attending", "declined", "tentative"] as const)
    .default("pending"),
  dietary_restrictions: z.array(z.string()).default([]),
  plus_ones: z.coerce.number().int().min(0).default(0),
  table_number: z.coerce.number().int().min(0).nullable().optional().default(null),
  notes: z.string().max(1000).optional().default(""),
});

type GuestFormValues = z.infer<typeof guestFormSchema>;

const EMPTY: GuestFormValues = {
  full_name: "",
  email: "",
  phone: null,
  rsvp_status: "pending",
  dietary_restrictions: [],
  plus_ones: 0,
  table_number: null,
  notes: "",
};

const RSVP_STATUSES: GuestRsvpStatus[] = [
  "pending",
  "attending",
  "declined",
  "tentative",
];

/* ── Props ───────────────────────────────────────── */

export interface GuestFormProps {
  isOpen: boolean;
  onClose: () => void;
  initialData?: Guest;
  onSubmit: (data: CreateGuestRequest) => Promise<void>;
  submitting?: boolean;
}

export function GuestForm({
  isOpen,
  onClose,
  initialData,
  onSubmit,
  submitting = false,
}: GuestFormProps): React.JSX.Element {
  const isEdit = Boolean(initialData);

  const defaults: GuestFormValues = initialData
    ? {
        full_name: initialData.full_name,
        email: initialData.email,
        phone: initialData.phone,
        rsvp_status: initialData.rsvp_status,
        dietary_restrictions: initialData.dietary_restrictions,
        plus_ones: initialData.plus_ones,
        table_number: initialData.table_number,
        notes: initialData.notes,
      }
    : EMPTY;

  const [values, setValues] = useState<GuestFormValues>(defaults);
  const [errors, setErrors] = useState<Partial<Record<keyof GuestFormValues, string>>>(
    {},
  );
  const [dietaryInput, setDietaryInput] = useState("");

  const set = <K extends keyof GuestFormValues>(key: K, val: GuestFormValues[K]) => {
    setValues((p) => ({ ...p, [key]: val }));
    setErrors((p) => ({ ...p, [key]: undefined }));
  };

  const addDietary = () => {
    const trimmed = dietaryInput.trim();
    if (trimmed && !values.dietary_restrictions.includes(trimmed)) {
      set("dietary_restrictions", [...values.dietary_restrictions, trimmed]);
    }
    setDietaryInput("");
  };

  const removeDietary = (item: string) => {
    set(
      "dietary_restrictions",
      values.dietary_restrictions.filter((d) => d !== item),
    );
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const result = guestFormSchema.safeParse(values);
    if (!result.success) {
      const fe: Partial<Record<keyof GuestFormValues, string>> = {};
      result.error.issues.forEach((err) => {
        const f = err.path[0] as keyof GuestFormValues;
        if (!fe[f]) fe[f] = err.message;
      });
      setErrors(fe);
      return;
    }
    await onSubmit(result.data as CreateGuestRequest);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEdit ? "Edit Guest" : "Add Guest"}
      description="Manage guest details and RSVP."
      className="max-w-2xl"
    >
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input
            label="Full Name"
            placeholder="Guest name"
            value={values.full_name}
            onChange={(e) => set("full_name", e.target.value)}
            error={errors.full_name}
            required
          />
          <Input
            label="Email"
            type="email"
            placeholder="guest@example.com"
            value={values.email}
            onChange={(e) => set("email", e.target.value)}
            error={errors.email}
            required
          />
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <Input
            label="Phone"
            type="tel"
            placeholder="+1 (555) 123-4567"
            value={values.phone ?? ""}
            onChange={(e) => set("phone", e.target.value || null)}
          />
          <Input
            label="Plus Ones"
            type="number"
            min={0}
            value={String(values.plus_ones)}
            onChange={(e) => set("plus_ones", Number(e.target.value))}
          />
          <Input
            label="Table Number"
            type="number"
            min={0}
            value={values.table_number != null ? String(values.table_number) : ""}
            onChange={(e) =>
              set("table_number", e.target.value ? Number(e.target.value) : null)
            }
          />
        </div>

        <div className="w-full">
          <label
            htmlFor="rsvp_status"
            className="mb-1.5 block text-xs font-medium text-gray-300"
          >
            RSVP Status
          </label>
          <select
            id="rsvp_status"
            value={values.rsvp_status}
            onChange={(e) => set("rsvp_status", e.target.value as GuestRsvpStatus)}
            className="w-full rounded-lg border border-white/20 bg-white/5 px-3.5 py-2 text-sm text-white backdrop-blur-md transition-colors focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            {RSVP_STATUSES.map((s) => (
              <option key={s} value={s} className="bg-gray-900">
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {/* Dietary restrictions tags */}
        <div className="w-full">
          <label
            htmlFor="dietary-input"
            className="mb-1.5 block text-xs font-medium text-gray-300"
          >
            Dietary Restrictions
          </label>
          <div className="flex gap-2">
            <input
              id="dietary-input"
              type="text"
              value={dietaryInput}
              onChange={(e) => setDietaryInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addDietary();
                }
              }}
              placeholder="Type and press Enter"
              className="flex-1 rounded-lg border border-white/20 bg-white/5 px-3.5 py-2 text-sm text-white placeholder-gray-400 backdrop-blur-md transition-colors focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              aria-label="Add dietary restriction"
            />
            <Button type="button" variant="secondary" onClick={addDietary}>
              Add
            </Button>
          </div>
          {values.dietary_restrictions.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {values.dietary_restrictions.map((d) => (
                <span
                  key={d}
                  className="inline-flex items-center gap-1 rounded-full bg-indigo-500/20 px-2.5 py-0.5 text-xs text-indigo-300"
                >
                  {d}
                  <button
                    type="button"
                    onClick={() => removeDietary(d)}
                    className="ml-0.5 text-indigo-400 hover:text-white"
                    aria-label={`Remove ${d}`}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        <Input
          label="Notes"
          placeholder="Optional notes"
          value={values.notes}
          onChange={(e) => set("notes", e.target.value)}
          error={errors.notes}
        />

        <div className="flex justify-end gap-3 border-t border-white/10 pt-4">
          <Button variant="ghost" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting ? "Saving…" : isEdit ? "Update" : "Add Guest"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
