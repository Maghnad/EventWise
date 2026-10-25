"use client";

import { useState, type FormEvent } from "react";
import { z } from "zod";
import { Input, Button, Modal } from "@/shared/components";
import type {
  CreateTimelineTaskRequest,
  TaskStatus,
  TimelineTask,
} from "@/shared/contracts";

/* ── Zod Schema ──────────────────────────────────── */

export const timelineTaskSchema = z.object({
  title: z.string().min(1, "Title is required").max(200),
  description: z.string().max(2000).optional().default(""),
  start_time: z.string().min(1, "Start time is required"),
  end_time: z.string().min(1, "End time is required"),
  assigned_to: z.string().nullable().optional().default(null),
  status: z
    .enum(["pending", "in_progress", "completed", "delayed"] as const)
    .default("pending"),
  category: z.string().max(100).optional().default(""),
  order_index: z.coerce.number().int().min(0).default(0),
});

type TimelineFormValues = z.infer<typeof timelineTaskSchema>;

const EMPTY: TimelineFormValues = {
  title: "",
  description: "",
  start_time: "",
  end_time: "",
  assigned_to: null,
  status: "pending",
  category: "",
  order_index: 0,
};

const STATUSES: TaskStatus[] = ["pending", "in_progress", "completed", "delayed"];

/* ── Props ───────────────────────────────────────── */

export interface TimelineFormProps {
  isOpen: boolean;
  onClose: () => void;
  initialData?: TimelineTask;
  onSubmit: (data: CreateTimelineTaskRequest) => Promise<void>;
  submitting?: boolean;
}

export function TimelineForm({
  isOpen,
  onClose,
  initialData,
  onSubmit,
  submitting = false,
}: TimelineFormProps): React.JSX.Element {
  const isEdit = Boolean(initialData);

  const defaults: TimelineFormValues = initialData
    ? {
        title: initialData.title,
        description: initialData.description,
        start_time: initialData.start_time.slice(0, 16),
        end_time: initialData.end_time.slice(0, 16),
        assigned_to: initialData.assigned_to,
        status: initialData.status,
        category: initialData.category,
        order_index: initialData.order_index,
      }
    : EMPTY;

  const [values, setValues] = useState<TimelineFormValues>(defaults);
  const [errors, setErrors] = useState<Partial<Record<keyof TimelineFormValues, string>>>(
    {},
  );

  const set = <K extends keyof TimelineFormValues>(
    key: K,
    val: TimelineFormValues[K],
  ) => {
    setValues((p) => ({ ...p, [key]: val }));
    setErrors((p) => ({ ...p, [key]: undefined }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const result = timelineTaskSchema.safeParse(values);
    if (!result.success) {
      const fe: Partial<Record<keyof TimelineFormValues, string>> = {};
      result.error.issues.forEach((err) => {
        const f = err.path[0] as keyof TimelineFormValues;
        if (!fe[f]) fe[f] = err.message;
      });
      setErrors(fe);
      return;
    }
    await onSubmit(result.data as CreateTimelineTaskRequest);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEdit ? "Edit Task" : "Add Task"}
      description="Schedule a task on your event timeline."
    >
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <Input
          label="Title"
          placeholder="Task title"
          value={values.title}
          onChange={(e) => set("title", e.target.value)}
          error={errors.title}
          required
        />

        <Input
          label="Description"
          placeholder="What needs to be done"
          value={values.description}
          onChange={(e) => set("description", e.target.value)}
          error={errors.description}
        />

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input
            label="Start Time"
            type="datetime-local"
            value={values.start_time}
            onChange={(e) => set("start_time", e.target.value)}
            error={errors.start_time}
            required
          />
          <Input
            label="End Time"
            type="datetime-local"
            value={values.end_time}
            onChange={(e) => set("end_time", e.target.value)}
            error={errors.end_time}
            required
          />
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <Input
            label="Assigned To"
            placeholder="Person name"
            value={values.assigned_to ?? ""}
            onChange={(e) => set("assigned_to", e.target.value || null)}
          />
          <Input
            label="Category"
            placeholder="e.g. Setup, Catering"
            value={values.category}
            onChange={(e) => set("category", e.target.value)}
          />
          <Input
            label="Order"
            type="number"
            min={0}
            value={String(values.order_index)}
            onChange={(e) => set("order_index", Number(e.target.value))}
          />
        </div>

        <div className="w-full">
          <label
            htmlFor="task-status"
            className="mb-1.5 block text-xs font-medium text-gray-300"
          >
            Status
          </label>
          <select
            id="task-status"
            value={values.status}
            onChange={(e) => set("status", e.target.value as TaskStatus)}
            className="w-full rounded-lg border border-white/20 bg-white/5 px-3.5 py-2 text-sm text-white backdrop-blur-md transition-colors focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            {STATUSES.map((s) => (
              <option key={s} value={s} className="bg-gray-900">
                {s.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase())}
              </option>
            ))}
          </select>
        </div>

        <div className="flex justify-end gap-3 border-t border-white/10 pt-4">
          <Button variant="ghost" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting ? "Saving…" : isEdit ? "Update" : "Add Task"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
