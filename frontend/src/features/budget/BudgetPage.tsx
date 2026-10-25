"use client";

import { useState, useCallback } from "react";
import { useBudget } from "./useBudget";
import { BudgetForm } from "./BudgetForm";
import { WhatIfPanel } from "./WhatIfPanel";
import { Button, Card } from "@/shared/components";
import type {
  BudgetItem,
  BudgetItemStatus,
  CreateBudgetItemRequest,
  UpdateBudgetItemRequest,
} from "@/shared/contracts";

/* ── Status colours ──────────────────────────────── */

const STATUS_COLORS: Record<BudgetItemStatus, string> = {
  planned: "bg-gray-500/20 text-gray-300",
  deposit_paid: "bg-amber-500/20 text-amber-300",
  paid: "bg-emerald-500/20 text-emerald-300",
  cancelled: "bg-red-500/20 text-red-300",
};

/* ── Props ───────────────────────────────────────── */

export interface BudgetPageProps {
  eventId: string;
}

export function BudgetPage({ eventId }: BudgetPageProps): React.JSX.Element {
  const { overview, loading, error, refetch, createItem, updateItem, deleteItem } =
    useBudget(eventId);

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<BudgetItem | undefined>();
  const [submitting, setSubmitting] = useState(false);
  const [showSimulator, setShowSimulator] = useState(false);

  const openCreate = useCallback(() => {
    setEditing(undefined);
    setFormOpen(true);
  }, []);

  const openEdit = useCallback((item: BudgetItem) => {
    setEditing(item);
    setFormOpen(true);
  }, []);

  const handleSubmit = async (data: CreateBudgetItemRequest) => {
    try {
      setSubmitting(true);
      if (editing) {
        await updateItem(editing.id, data as UpdateBudgetItemRequest);
      } else {
        await createItem(data);
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

  if (error || !overview) {
    return (
      <Card className="mx-auto mt-16 max-w-md text-center">
        <p className="text-red-400" role="alert">
          Failed to load budget — {error?.message ?? "Unknown error"}
        </p>
        <Button className="mt-4" onClick={refetch}>
          Retry
        </Button>
      </Card>
    );
  }

  const pctUsed =
    overview.total_budget > 0
      ? Math.round((overview.total_spent / overview.total_budget) * 100)
      : 0;

  return (
    <section aria-label="Budget">
      {/* Summary cards */}
      <div className="mb-8 grid gap-4 sm:grid-cols-4">
        <Card>
          <p className="text-xs uppercase tracking-wider text-gray-500">Total Budget</p>
          <p className="mt-1 text-2xl font-bold text-white">
            {overview.currency} {overview.total_budget.toLocaleString()}
          </p>
        </Card>
        <Card>
          <p className="text-xs uppercase tracking-wider text-gray-500">Allocated</p>
          <p className="mt-1 text-2xl font-bold text-blue-400">
            {overview.currency} {overview.total_allocated.toLocaleString()}
          </p>
        </Card>
        <Card>
          <p className="text-xs uppercase tracking-wider text-gray-500">Spent</p>
          <p className="mt-1 text-2xl font-bold text-amber-400">
            {overview.currency} {overview.total_spent.toLocaleString()}
          </p>
        </Card>
        <Card>
          <p className="text-xs uppercase tracking-wider text-gray-500">Remaining</p>
          <p
            className={`mt-1 text-2xl font-bold ${overview.remaining_budget >= 0 ? "text-emerald-400" : "text-red-400"}`}
          >
            {overview.currency} {overview.remaining_budget.toLocaleString()}
          </p>
        </Card>
      </div>

      {/* Progress bar */}
      <div className="mb-8">
        <div className="mb-1 flex items-center justify-between text-xs text-gray-400">
          <span>Budget usage</span>
          <span>{pctUsed}%</span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
          <div
            className={`h-full rounded-full transition-all ${pctUsed > 90 ? "bg-red-500" : pctUsed > 70 ? "bg-amber-500" : "bg-emerald-500"}`}
            style={{ width: `${Math.min(pctUsed, 100)}%` }}
          />
        </div>
      </div>

      {/* Header */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <h2 className="text-xl font-bold text-white">Budget Overview & Planning</h2>
        <div className="flex items-center gap-3">
          <Button
            variant={showSimulator ? "primary" : "secondary"}
            onClick={() => setShowSimulator((prev) => !prev)}
            aria-label="Toggle What-If Scenario Simulator"
          >
            {showSimulator ? "Hide Simulator" : "🔮 What-If Simulator"}
          </Button>
          <Button onClick={openCreate} aria-label="Add budget item">
            + Add Item
          </Button>
        </div>
      </div>

      {/* What-If Scenario Simulator */}
      {showSimulator && (
        <div className="mb-10 animate-fadeIn">
          <WhatIfPanel
            eventId={eventId}
            initialBudget={overview.total_budget}
            overview={overview}
          />
        </div>
      )}

      {/* Items table */}
      {overview.items.length === 0 ? (
        <Card className="py-16 text-center">
          <p className="mb-3 text-4xl">💰</p>
          <p className="text-gray-400">No budget items yet.</p>
        </Card>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-white/10">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-white/10 bg-white/5">
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-400">
                  Category
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-400">
                  Name
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase text-gray-400">
                  Estimated
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase text-gray-400">
                  Actual
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase text-gray-400">
                  Paid
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium uppercase text-gray-400">
                  Status
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase text-gray-400">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {overview.items.map((item) => (
                <tr
                  key={item.id}
                  className="border-b border-white/5 transition-colors hover:bg-white/[0.03]"
                >
                  <td className="px-4 py-3 text-gray-300">{item.category}</td>
                  <td className="px-4 py-3 font-medium text-white">{item.name}</td>
                  <td className="px-4 py-3 text-right text-gray-300">
                    {item.estimated_cost.toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-300">
                    {item.actual_cost?.toLocaleString() ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-300">
                    {item.paid_amount.toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[item.status]}`}
                    >
                      {item.status.replace("_", " ")}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="ghost"
                        className="px-2 py-1 text-xs"
                        onClick={() => openEdit(item)}
                        aria-label={`Edit ${item.name}`}
                      >
                        Edit
                      </Button>
                      <Button
                        variant="danger"
                        className="px-2 py-1 text-xs"
                        onClick={() => deleteItem(item.id)}
                        aria-label={`Delete ${item.name}`}
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

      <BudgetForm
        isOpen={formOpen}
        onClose={() => setFormOpen(false)}
        initialData={editing}
        onSubmit={handleSubmit}
        submitting={submitting}
      />
    </section>
  );
}
