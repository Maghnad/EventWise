"use client";

import { useState, type FormEvent } from "react";
import { z } from "zod";
import { Input, Button, Modal } from "@/shared/components";
import type {
  CreateVendorChecklistItemRequest,
  VendorChecklistItem,
} from "@/shared/contracts";

/* ── Zod Schema ──────────────────────────────────── */

export const vendorChecklistSchema = z.object({
  vendor_category: z.string().min(1, "Category is required").max(100),
  task_name: z.string().min(1, "Task name is required").max(200),
  is_completed: z.boolean().default(false),
  due_date: z.string().nullable().optional().default(null),
  assigned_vendor_name: z.string().nullable().optional().default(null),
  notes: z.string().max(1000).optional().default(""),
});

type VendorFormValues = z.infer<typeof vendorChecklistSchema>;

const EMPTY: VendorFormValues = {
  vendor_category: "",
  task_name: "",
  is_completed: false,
  due_date: null,
  assigned_vendor_name: null,
  notes: "",
};

/* ── Props ───────────────────────────────────────── */

export interface VendorFormProps {
  isOpen: boolean;
  onClose: () => void;
  initialData?: VendorChecklistItem;
  onSubmit: (data: CreateVendorChecklistItemRequest) => Promise<void>;
  submitting?: boolean;
}

export function VendorForm({
  isOpen,
  onClose,
  initialData,
  onSubmit,
  submitting = false,
}: VendorFormProps): React.JSX.Element {
  const isEdit = Boolean(initialData);

  const defaults: VendorFormValues = initialData
    ? {
        vendor_category: initialData.vendor_category,
        task_name: initialData.task_name,
        is_completed: initialData.is_completed,
        due_date: initialData.due_date?.slice(0, 10) ?? null,
        assigned_vendor_name: initialData.assigned_vendor_name,
        notes: initialData.notes,
      }
    : EMPTY;

  const [values, setValues] = useState<VendorFormValues>(defaults);
  const [errors, setErrors] = useState<Partial<Record<keyof VendorFormValues, string>>>(
    {},
  );

  const set = <K extends keyof VendorFormValues>(key: K, val: VendorFormValues[K]) => {
    setValues((p) => ({ ...p, [key]: val }));
    setErrors((p) => ({ ...p, [key]: undefined }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const result = vendorChecklistSchema.safeParse(values);
    if (!result.success) {
      const fe: Partial<Record<keyof VendorFormValues, string>> = {};
      result.error.issues.forEach((err) => {
        const f = err.path[0] as keyof VendorFormValues;
        if (!fe[f]) fe[f] = err.message;
      });
      setErrors(fe);
      return;
    }
    await onSubmit(result.data as CreateVendorChecklistItemRequest);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEdit ? "Edit Checklist Item" : "Add Checklist Item"}
      description="Track vendor tasks for your event."
    >
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input
            label="Vendor Category"
            placeholder="e.g. Photography, Catering"
            value={values.vendor_category}
            onChange={(e) => set("vendor_category", e.target.value)}
            error={errors.vendor_category}
            required
          />
          <Input
            label="Task Name"
            placeholder="What needs to be done"
            value={values.task_name}
            onChange={(e) => set("task_name", e.target.value)}
            error={errors.task_name}
            required
          />
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input
            label="Due Date"
            type="date"
            value={values.due_date ?? ""}
            onChange={(e) => set("due_date", e.target.value || null)}
          />
          <Input
            label="Assigned Vendor"
            placeholder="Vendor name"
            value={values.assigned_vendor_name ?? ""}
            onChange={(e) => set("assigned_vendor_name", e.target.value || null)}
          />
        </div>

        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            id="is_completed"
            checked={values.is_completed}
            onChange={(e) => set("is_completed", e.target.checked)}
            className="h-4 w-4 rounded border-white/20 bg-white/5 text-indigo-500 focus:ring-indigo-500"
          />
          <label htmlFor="is_completed" className="text-sm text-gray-300">
            Mark as completed
          </label>
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
            {submitting ? "Saving…" : isEdit ? "Update" : "Add Item"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
