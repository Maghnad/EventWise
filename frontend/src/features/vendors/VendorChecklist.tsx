"use client";

import React from "react";
import { Button, Card } from "@/shared/components";
import type { VendorChecklistItem, VendorChecklistResponse } from "@/shared/contracts";

export interface VendorChecklistProps {
  checklist: VendorChecklistResponse;
  onToggleComplete?: (item: VendorChecklistItem) => void;
  onEditItem?: (item: VendorChecklistItem) => void;
  onDeleteItem?: (itemId: string) => void;
  onAddItem?: () => void;
  className?: string;
}

export function VendorChecklist({
  checklist,
  onToggleComplete,
  onEditItem,
  onDeleteItem,
  onAddItem,
  className = "",
}: VendorChecklistProps): React.JSX.Element {
  const pct =
    checklist.total_items > 0
      ? Math.round((checklist.completed_items / checklist.total_items) * 100)
      : 0;

  // Group items by category
  const grouped = checklist.items.reduce<Record<string, VendorChecklistItem[]>>(
    (acc, item) => {
      const cat = item.vendor_category || "General";
      if (!acc[cat]) acc[cat] = [];
      acc[cat].push(item);
      return acc;
    },
    {},
  );

  return (
    <section aria-label="Vendor Checklist" className={`space-y-8 ${className}`}>
      {/* Summary */}
      <div className="grid gap-4 sm:grid-cols-3">
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
      <div>
        <div
          className="h-2 w-full overflow-hidden rounded-full bg-white/10"
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Vendor deliverables progress"
        >
          <div
            className="h-full rounded-full bg-emerald-500 transition-all duration-300"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* Header */}
      {onAddItem && (
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-white">Vendor Deliverables</h2>
          <Button onClick={onAddItem} aria-label="Add checklist item">
            + Add Item
          </Button>
        </div>
      )}

      {/* Grouped items */}
      {checklist.items.length === 0 ? (
        <Card className="py-16 text-center">
          <p className="mb-3 text-4xl">🤝</p>
          <p className="text-gray-400">No checklist items yet.</p>
        </Card>
      ) : (
        <div className="space-y-6">
          {Object.entries(grouped).map(([category, items]) => (
            <div key={category} className="space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                {category} ({items.filter((i) => i.is_completed).length}/{items.length})
              </h3>

              <div className="space-y-2">
                {items.map((item) => (
                  <Card
                    key={item.id}
                    className="flex flex-col gap-3 p-4 transition-colors hover:bg-white/[0.03] sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div className="flex items-start gap-3">
                      {onToggleComplete && (
                        <button
                          type="button"
                          onClick={() => onToggleComplete(item)}
                          className={`mt-1 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded border transition-colors ${
                            item.is_completed
                              ? "border-emerald-500 bg-emerald-500/20 text-emerald-400"
                              : "border-white/20 hover:border-white/40"
                          }`}
                          aria-label={`Toggle completion for ${item.task_name}`}
                        >
                          {item.is_completed ? "✓" : ""}
                        </button>
                      )}

                      <div>
                        <p
                          className={`text-sm font-medium ${
                            item.is_completed
                              ? "text-gray-400 line-through"
                              : "text-white"
                          }`}
                        >
                          {item.task_name}
                        </p>
                        {item.notes && (
                          <p className="mt-0.5 text-xs text-gray-400">{item.notes}</p>
                        )}
                        <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs text-gray-500">
                          {item.due_date && (
                            <span>
                              Due:{" "}
                              {new Date(item.due_date).toLocaleDateString([], {
                                month: "short",
                                day: "numeric",
                              })}
                            </span>
                          )}
                          {item.assigned_vendor_name && (
                            <span>• Vendor: {item.assigned_vendor_name}</span>
                          )}
                        </div>
                      </div>
                    </div>

                    {(onEditItem || onDeleteItem) && (
                      <div className="flex items-center gap-2 self-end sm:self-center">
                        {onEditItem && (
                          <Button
                            variant="ghost"
                            className="px-2 py-1 text-xs"
                            onClick={() => onEditItem(item)}
                            aria-label={`Edit ${item.task_name}`}
                          >
                            Edit
                          </Button>
                        )}
                        {onDeleteItem && (
                          <Button
                            variant="danger"
                            className="px-2 py-1 text-xs"
                            onClick={() => onDeleteItem(item.id)}
                            aria-label={`Delete ${item.task_name}`}
                          >
                            ✕
                          </Button>
                        )}
                      </div>
                    )}
                  </Card>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
