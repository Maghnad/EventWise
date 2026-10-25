"use client";

import { useState, useCallback } from "react";
import { useVendors } from "./useVendors";
import { VendorForm } from "./VendorForm";
import { Button, Card } from "@/shared/components";
import type {
  CreateVendorChecklistItemRequest,
  UpdateVendorChecklistItemRequest,
  VendorChecklistItem,
} from "@/shared/contracts";

/* ── Props ───────────────────────────────────────── */

export interface VendorsPageProps {
  eventId: string;
}

export function VendorsPage({ eventId }: VendorsPageProps): React.JSX.Element {
  const { checklist, loading, error, refetch, createItem, updateItem, deleteItem } =
    useVendors(eventId);

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<VendorChecklistItem | undefined>();
  const [submitting, setSubmitting] = useState(false);

  const openCreate = useCallback(() => {
    setEditing(undefined);
    setFormOpen(true);
  }, []);

  const openEdit = useCallback((item: VendorChecklistItem) => {
    setEditing(item);
    setFormOpen(true);
  }, []);

  const handleSubmit = async (data: CreateVendorChecklistItemRequest) => {
    try {
      setSubmitting(true);
      if (editing) {
        await updateItem(editing.id, data as UpdateVendorChecklistItemRequest);
      } else {
        await createItem(data);
      }
      setFormOpen(false);
    } finally {
      setSubmitting(false);
    }
  };

  const toggleCompleted = async (item: VendorChecklistItem) => {
    await updateItem(item.id, { is_completed: !item.is_completed });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
      </div>
    );
  }

  if (error || !checklist) {
    return (
      <Card className="mx-auto mt-16 max-w-md text-center">
        <p className="text-red-400" role="alert">
          Failed to load checklist — {error?.message ?? "Unknown error"}
        </p>
        <Button className="mt-4" onClick={refetch}>
          Retry
        </Button>
      </Card>
    );
  }

  const pct =
    checklist.total_items > 0
      ? Math.round((checklist.completed_items / checklist.total_items) * 100)
      : 0;

  /* Group by category */
  const grouped = checklist.items.reduce<Record<string, VendorChecklistItem[]>>(
    (acc, item) => {
      const cat = item.vendor_category;
      if (!acc[cat]) acc[cat] = [];
      acc[cat].push(item);
      return acc;
    },
    {},
  );

  return (
    <section aria-label="Vendor Checklist">
      {/* Summary */}
      <div className="mb-8 grid gap-4 sm:grid-cols-3">
        <Card>
          <p className="text-xs uppercase tracking-wider text-gray-500">Total Items</p>
          <p className="mt-1 text-2xl font-bold text-white">{checklist.total_items}</p>
        </Card>
        <Card>
          <p className="text-xs uppercase tracking-wider text-gray-500">Completed</p>
          <p className="mt-1 text-2xl font-bold text-emerald-400">
            {checklist.completed_items}
          </p>
        </Card>
        <Card>
          <p className="text-xs uppercase tracking-wider text-gray-500">Progress</p>
          <p className="mt-1 text-2xl font-bold text-indigo-400">{pct}%</p>
        </Card>
      </div>

      {/* Progress bar */}
      <div className="mb-8">
        <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
          <div
            className="h-full rounded-full bg-emerald-500 transition-all"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Vendor Checklist</h2>
        <Button onClick={openCreate} aria-label="Add checklist item">
          + Add Item
        </Button>
      </div>

      {/* Grouped items */}
      {checklist.items.length === 0 ? (
        <Card className="py-16 text-center">
          <p className="mb-3 text-4xl">🤝</p>
          <p className="text-gray-400">No checklist items yet.</p>
        </Card>
      ) : (
        <div className="space-y-6">
          {Object.entries(grouped).map(([category, items]) => (
            <div key={category}>
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-gray-400">
                {category}
              </h3>
              <div className="space-y-2">
                {items.map((item) => (
                  <Card
                    key={item.id}
                    className="flex items-center gap-4 transition-all hover:border-indigo-500/30"
                  >
                    {/* Checkbox */}
                    <button
                      type="button"
                      onClick={() => toggleCompleted(item)}
                      className={`flex h-6 w-6 flex-shrink-0 items-center justify-center rounded border transition-colors ${
                        item.is_completed
                          ? "border-emerald-500 bg-emerald-500/20 text-emerald-400"
                          : "border-white/20 bg-white/5 text-transparent hover:border-white/40"
                      }`}
                      aria-label={`Toggle ${item.task_name} completion`}
                    >
                      {item.is_completed && "✓"}
                    </button>

                    {/* Content */}
                    <div className="min-w-0 flex-1">
                      <p
                        className={`truncate font-medium ${
                          item.is_completed ? "text-gray-500 line-through" : "text-white"
                        }`}
                      >
                        {item.task_name}
                      </p>
                      <div className="mt-0.5 flex gap-3 text-xs text-gray-500">
                        {item.assigned_vendor_name && (
                          <span>{item.assigned_vendor_name}</span>
                        )}
                        {item.due_date && (
                          <span>
                            Due:{" "}
                            {new Date(item.due_date).toLocaleDateString("en-US", {
                              month: "short",
                              day: "numeric",
                            })}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        className="px-2 py-1 text-xs"
                        onClick={() => openEdit(item)}
                        aria-label={`Edit ${item.task_name}`}
                      >
                        Edit
                      </Button>
                      <Button
                        variant="danger"
                        className="px-2 py-1 text-xs"
                        onClick={() => deleteItem(item.id)}
                        aria-label={`Delete ${item.task_name}`}
                      >
                        ✕
                      </Button>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <VendorForm
        isOpen={formOpen}
        onClose={() => setFormOpen(false)}
        initialData={editing}
        onSubmit={handleSubmit}
        submitting={submitting}
      />
    </section>
  );
}
