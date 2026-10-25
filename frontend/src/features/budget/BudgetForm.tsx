"use client";

import { useState, type FormEvent } from "react";
import { z } from "zod";
import { Input, Button, Modal } from "@/shared/components";
import type {
  BudgetItem,
  BudgetItemStatus,
  CreateBudgetItemRequest,
} from "@/shared/contracts";

/* ── Zod Schema ──────────────────────────────────── */

export const budgetItemSchema = z.object({
  category: z.string().min(1, "Category is required").max(100),
  name: z.string().min(1, "Name is required").max(200),
  estimated_cost: z.coerce.number().min(0, "Must be ≥ 0"),
  actual_cost: z.coerce.number().min(0).nullable().optional(),
  paid_amount: z.coerce.number().min(0).default(0),
  status: z
    .enum(["planned", "deposit_paid", "paid", "cancelled"] as const)
    .default("planned"),
  notes: z.string().max(1000).optional().default(""),
});

type BudgetFormValues = z.infer<typeof budgetItemSchema>;

const EMPTY: BudgetFormValues = {
  category: "",
  name: "",
  estimated_cost: 0,
  actual_cost: null,
  paid_amount: 0,
  status: "planned",
  notes: "",
};

const STATUSES: BudgetItemStatus[] = ["planned", "deposit_paid", "paid", "cancelled"];

/* ── Props ───────────────────────────────────────── */

export interface BudgetFormProps {
  isOpen: boolean;
  onClose: () => void;
  initialData?: BudgetItem;
  onSubmit: (data: CreateBudgetItemRequest) => Promise<void>;
  submitting?: boolean;
}

export function BudgetForm({
  isOpen,
  onClose,
  initialData,
  onSubmit,
  submitting = false,
}: BudgetFormProps): React.JSX.Element {
  const isEdit = Boolean(initialData);

  const defaults: BudgetFormValues = initialData
    ? {
        category: initialData.category,
        name: initialData.name,
        estimated_cost: initialData.estimated_cost,
        actual_cost: initialData.actual_cost,
        paid_amount: initialData.paid_amount,
        status: initialData.status,
        notes: initialData.notes,
      }
    : EMPTY;

  const [values, setValues] = useState<BudgetFormValues>(defaults);
  const [errors, setErrors] = useState<Partial<Record<keyof BudgetFormValues, string>>>(
    {},
  );

  const set = <K extends keyof BudgetFormValues>(key: K, val: BudgetFormValues[K]) => {
    setValues((p) => ({ ...p, [key]: val }));
    setErrors((p) => ({ ...p, [key]: undefined }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const result = budgetItemSchema.safeParse(values);
    if (!result.success) {
      const fe: Partial<Record<keyof BudgetFormValues, string>> = {};
      result.error.issues.forEach((err) => {
        const f = err.path[0] as keyof BudgetFormValues;
        if (!fe[f]) fe[f] = err.message;
      });
      setErrors(fe);
      return;
    }
    await onSubmit(result.data as CreateBudgetItemRequest);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEdit ? "Edit Budget Item" : "Add Budget Item"}
      description="Track individual cost items for your event."
    >
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input
            label="Category"
            placeholder="e.g. Venue, Catering"
            value={values.category}
            onChange={(e) => set("category", e.target.value)}
            error={errors.category}
            required
          />
          <Input
            label="Name"
            placeholder="Item name"
            value={values.name}
            onChange={(e) => set("name", e.target.value)}
            error={errors.name}
            required
          />
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <Input
            label="Estimated Cost"
            type="number"
            min={0}
            step={0.01}
            value={String(values.estimated_cost)}
            onChange={(e) => set("estimated_cost", Number(e.target.value))}
            error={errors.estimated_cost}
          />
          <Input
            label="Actual Cost"
            type="number"
            min={0}
            step={0.01}
            value={values.actual_cost != null ? String(values.actual_cost) : ""}
            onChange={(e) =>
              set("actual_cost", e.target.value ? Number(e.target.value) : null)
            }
            error={errors.actual_cost}
          />
          <Input
            label="Paid Amount"
            type="number"
            min={0}
            step={0.01}
            value={String(values.paid_amount)}
            onChange={(e) => set("paid_amount", Number(e.target.value))}
            error={errors.paid_amount}
          />
        </div>

        <div className="w-full">
          <label
            htmlFor="budget-status"
            className="mb-1.5 block text-xs font-medium text-gray-300"
          >
            Status
          </label>
          <select
            id="budget-status"
            value={values.status}
            onChange={(e) => set("status", e.target.value as BudgetItemStatus)}
            className="w-full rounded-lg border border-white/20 bg-white/5 px-3.5 py-2 text-sm text-white backdrop-blur-md transition-colors focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            {STATUSES.map((s) => (
              <option key={s} value={s} className="bg-gray-900">
                {s.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase())}
              </option>
            ))}
          </select>
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
