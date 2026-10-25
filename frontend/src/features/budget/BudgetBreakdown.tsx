"use client";

import React from "react";
import { Button, Card } from "@/shared/components";
import type { BudgetItem, BudgetItemStatus, BudgetOverviewResponse } from "@/shared/contracts";

const STATUS_COLORS: Record<BudgetItemStatus, string> = {
  planned: "bg-gray-500/20 text-gray-300",
  deposit_paid: "bg-amber-500/20 text-amber-300",
  paid: "bg-emerald-500/20 text-emerald-300",
  cancelled: "bg-red-500/20 text-red-300",
};

export interface BudgetBreakdownProps {
  overview: BudgetOverviewResponse;
  onEditItem?: (item: BudgetItem) => void;
  onDeleteItem?: (itemId: string) => void;
  onAddItem?: () => void;
  className?: string;
}

export function BudgetBreakdown({
  overview,
  onEditItem,
  onDeleteItem,
  onAddItem,
  className = "",
}: BudgetBreakdownProps): React.JSX.Element {
  const pctUsed =
    overview.total_budget > 0
      ? Math.round((overview.total_spent / overview.total_budget) * 100)
      : 0;

  return (
    <section aria-label="Budget Breakdown" className={`space-y-8 ${className}`}>
      {/* Summary cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
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
            className={`mt-1 text-2xl font-bold ${
              overview.remaining_budget >= 0 ? "text-emerald-400" : "text-red-400"
            }`}
          >
            {overview.currency} {overview.remaining_budget.toLocaleString()}
          </p>
        </Card>
      </div>

      {/* Progress bar */}
      <div>
        <div className="mb-1 flex items-center justify-between text-xs text-gray-400">
          <span>Budget usage</span>
          <span>{pctUsed}%</span>
        </div>
        <div
          className="h-2 w-full overflow-hidden rounded-full bg-white/10"
          role="progressbar"
          aria-valuenow={pctUsed}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Overall budget usage progress"
        >
          <div
            className={`h-full rounded-full transition-all duration-300 ${
              pctUsed > 90 ? "bg-red-500" : pctUsed > 70 ? "bg-amber-500" : "bg-emerald-500"
            }`}
            style={{ width: `${Math.min(pctUsed, 100)}%` }}
          />
        </div>
      </div>

      {/* Header & Add Button */}
      {onAddItem && (
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-white">Budget Line Items</h2>
          <Button onClick={onAddItem} aria-label="Add budget item">
            + Add Item
          </Button>
        </div>
      )}

      {/* Table */}
      {overview.items.length === 0 ? (
        <Card className="py-16 text-center">
          <p className="mb-3 text-4xl">💰</p>
          <p className="text-gray-400">No budget items recorded yet.</p>
        </Card>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-white/10">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-white/10 bg-white/5">
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-400">
                  Category
                </th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-400">
                  Name
                </th>
                <th scope="col" className="px-4 py-3 text-right text-xs font-medium uppercase text-gray-400">
                  Estimated
                </th>
                <th scope="col" className="px-4 py-3 text-right text-xs font-medium uppercase text-gray-400">
                  Actual
                </th>
                <th scope="col" className="px-4 py-3 text-right text-xs font-medium uppercase text-gray-400">
                  Paid
                </th>
                <th scope="col" className="px-4 py-3 text-center text-xs font-medium uppercase text-gray-400">
                  Status
                </th>
                {(onEditItem || onDeleteItem) && (
                  <th scope="col" className="px-4 py-3 text-right text-xs font-medium uppercase text-gray-400">
                    Actions
                  </th>
                )}
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
                      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                        STATUS_COLORS[item.status]
                      }`}
                    >
                      {item.status.replace("_", " ")}
                    </span>
                  </td>
                  {(onEditItem || onDeleteItem) && (
                    <td className="px-4 py-3 text-right">
                      <div className="flex justify-end gap-2">
                        {onEditItem && (
                          <Button
                            variant="ghost"
                            className="px-2 py-1 text-xs"
                            onClick={() => onEditItem(item)}
                            aria-label={`Edit ${item.name}`}
                          >
                            Edit
                          </Button>
                        )}
                        {onDeleteItem && (
                          <Button
                            variant="danger"
                            className="px-2 py-1 text-xs"
                            onClick={() => onDeleteItem(item.id)}
                            aria-label={`Delete ${item.name}`}
                          >
                            ✕
                          </Button>
                        )}
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
