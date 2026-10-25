"use client";

import { useEffect, useRef, useState } from "react";
import { Button, Card } from "@/shared/components";
import type {
  BudgetOverviewResponse,
  WhatIfScenarioResponse,
} from "@/shared/contracts";
import { simulateWhatIfScenario } from "./budgetApi";

export interface WhatIfPanelProps {
  eventId: string;
  initialBudget: number;
  initialGuestCount?: number;
  overview?: BudgetOverviewResponse;
}

const VENDOR_SWAP_PRESETS = [
  "Prioritize Gourmet Catering & Craft Cocktails over Venue",
  "Upgrade to Live 7-Piece Band & Professional Audio Staging",
  "Focus on Luxury Floral Installations & Custom Tablescapes",
  "Cost-Conscious Buffet & Acoustic Duo (Maximize Savings)",
  "Heavy on Drone Videography & Multi-Angle Photography",
];

export function WhatIfPanel({
  eventId,
  initialBudget,
  initialGuestCount = 100,
  overview,
}: WhatIfPanelProps): React.JSX.Element {
  // Scenario simulation inputs
  const [adjustedBudget, setAdjustedBudget] = useState<number>(initialBudget);
  const [adjustedGuests, setAdjustedGuests] = useState<number>(initialGuestCount);
  const [vendorPriority, setVendorPriority] = useState<string>("");

  // Simulation output state
  const [scenarioData, setScenarioData] = useState<WhatIfScenarioResponse | null>(null);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Debounce timer reference
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Sync with initial props if they load later
  useEffect(() => {
    if (initialBudget > 0 && adjustedBudget === 0) {
      setAdjustedBudget(initialBudget);
    }
  }, [initialBudget, adjustedBudget]);

  // Debounced API call to /what-if endpoint
  useEffect(() => {
    if (!eventId || adjustedBudget <= 0 || adjustedGuests <= 0) return;

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    debounceTimerRef.current = setTimeout(async () => {
      setIsSimulating(true);
      setError(null);
      try {
        const res = await simulateWhatIfScenario(eventId, {
          adjusted_budget: adjustedBudget,
          adjusted_guest_count: adjustedGuests,
          vibe_adjustment: vendorPriority || undefined,
        });
        setScenarioData(res);
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Failed to simulate scenario";
        setError(message);
      } finally {
        setIsSimulating(false);
      }
    }, 450); // 450ms debounce

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [eventId, adjustedBudget, adjustedGuests, vendorPriority]);

  const handleReset = () => {
    setAdjustedBudget(initialBudget);
    setAdjustedGuests(initialGuestCount);
    setVendorPriority("");
  };

  const handleBudgetIncrement = (percent: number) => {
    setAdjustedBudget((prev) => Math.max(500, Math.round(prev * (1 + percent / 100))));
  };

  const handleGuestIncrement = (delta: number) => {
    setAdjustedGuests((prev) => Math.max(5, prev + delta));
  };

  // Build baseline comparison category map from overview if available
  const baselineCategoryMap = new Map<string, number>();
  if (overview?.items) {
    for (const item of overview.items) {
      const cat = item.category.toLowerCase().trim();
      const current = baselineCategoryMap.get(cat) || 0;
      baselineCategoryMap.set(cat, current + Number(item.estimated_cost || 0));
    }
  }

  return (
    <section
      aria-label="What-If Scenario Simulator"
      className="space-y-8 rounded-2xl border border-indigo-500/20 bg-gradient-to-b from-indigo-950/20 via-black/40 to-black/60 p-6 shadow-2xl backdrop-blur-xl sm:p-8"
    >
      {/* Header */}
      <div className="flex flex-col justify-between gap-4 border-b border-white/10 pb-6 sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-3">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/20 text-sm">
              🔮
            </span>
            <h2 className="text-xl font-bold tracking-tight text-white sm:text-2xl">
              What-If Scenario Simulator
            </h2>
          </div>
          <p className="mt-1.5 text-xs text-gray-400">
            Adjust guest count, budget limits, or swap vendor priorities to see instant reallocation diffs.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {isSimulating && (
            <span className="flex items-center gap-2 rounded-full bg-indigo-500/10 px-3 py-1 text-xs text-indigo-300">
              <span className="h-3 w-3 animate-spin rounded-full border-2 border-indigo-400 border-t-transparent" />
              Recalculating...
            </span>
          )}
          <Button
            variant="secondary"
            onClick={handleReset}
            className="text-xs px-3 py-1.5"
            aria-label="Reset simulation to baseline"
          >
            Reset to Baseline
          </Button>
        </div>
      </div>

      {/* Simulator Interactive Controls */}
      <div className="grid gap-8 lg:grid-cols-2">
        {/* 1. Guest Count Adjustment */}
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-5">
          <div className="flex items-center justify-between">
            <label
              htmlFor="guest-slider"
              className="text-xs font-semibold uppercase tracking-wider text-gray-300"
            >
              Simulated Guest Count
            </label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                id="guest-number-input"
                min={5}
                max={2000}
                value={adjustedGuests}
                onChange={(e) => setAdjustedGuests(Math.max(1, Number(e.target.value)))}
                className="w-20 rounded-lg border border-white/10 bg-black/60 px-2.5 py-1 text-right text-sm font-bold text-white focus:border-indigo-500 focus:outline-none"
                aria-label="Guest count exact value"
              />
              <span className="text-xs text-gray-400">guests</span>
            </div>
          </div>

          <div className="mt-4">
            <input
              id="guest-slider"
              type="range"
              min={10}
              max={Math.max(500, initialGuestCount * 2)}
              step={5}
              value={adjustedGuests}
              onChange={(e) => setAdjustedGuests(Number(e.target.value))}
              className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-white/10 accent-indigo-500 focus:outline-none"
              aria-valuemin={10}
              aria-valuemax={Math.max(500, initialGuestCount * 2)}
              aria-valuenow={adjustedGuests}
              aria-label="Adjust guest count slider"
            />
          </div>

          {/* Quick guest increments */}
          <div className="mt-4 flex flex-wrap gap-2">
            {[-25, -10, +10, +25, +50, +100].map((delta) => (
              <button
                key={delta}
                type="button"
                onClick={() => handleGuestIncrement(delta)}
                className="rounded-lg border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-gray-300 transition-colors hover:border-indigo-400 hover:text-white"
              >
                {delta > 0 ? `+${delta}` : delta} guests
              </button>
            ))}
          </div>
        </div>

        {/* 2. Total Budget Adjustment */}
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-5">
          <div className="flex items-center justify-between">
            <label
              htmlFor="budget-slider"
              className="text-xs font-semibold uppercase tracking-wider text-gray-300"
            >
              Simulated Total Budget
            </label>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-gray-400">$</span>
              <input
                type="number"
                id="budget-number-input"
                min={500}
                step={500}
                value={adjustedBudget}
                onChange={(e) => setAdjustedBudget(Math.max(100, Number(e.target.value)))}
                className="w-28 rounded-lg border border-white/10 bg-black/60 px-2.5 py-1 text-right text-sm font-bold text-white focus:border-indigo-500 focus:outline-none"
                aria-label="Total budget exact value"
              />
            </div>
          </div>

          <div className="mt-4">
            <input
              id="budget-slider"
              type="range"
              min={1000}
              max={Math.max(100000, initialBudget * 2.5)}
              step={500}
              value={adjustedBudget}
              onChange={(e) => setAdjustedBudget(Number(e.target.value))}
              className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-white/10 accent-indigo-500 focus:outline-none"
              aria-valuemin={1000}
              aria-valuemax={Math.max(100000, initialBudget * 2.5)}
              aria-valuenow={adjustedBudget}
              aria-label="Adjust budget slider"
            />
          </div>

          {/* Quick budget percentage modifiers */}
          <div className="mt-4 flex flex-wrap gap-2">
            {[-25, -15, -10, +10, +25, +50].map((pct) => (
              <button
                key={pct}
                type="button"
                onClick={() => handleBudgetIncrement(pct)}
                className="rounded-lg border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-gray-300 transition-colors hover:border-indigo-400 hover:text-white"
              >
                {pct > 0 ? `+${pct}%` : `${pct}%`}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 3. Vendor Type / Aesthetic Priority Shift ("Swap Vendor Type") */}
      <div className="rounded-xl border border-white/5 bg-white/[0.02] p-5">
        <span
          id="vendor-swap-label"
          className="mb-2 block text-xs font-semibold uppercase tracking-wider text-purple-300"
        >
          🔄 Swap Vendor Priority or Creative Direction
        </span>
        <p className="mb-3 text-xs text-gray-400">
          Rebalance allocations towards specific vendor categories or event experiences.
        </p>

        <div
          role="group"
          aria-labelledby="vendor-swap-label"
          className="mb-3 flex flex-wrap gap-2"
        >
          {VENDOR_SWAP_PRESETS.map((preset) => (
            <button
              key={preset}
              type="button"
              onClick={() => setVendorPriority(preset)}
              className={`rounded-lg border px-3 py-1.5 text-xs transition-all ${
                vendorPriority === preset
                  ? "border-purple-400 bg-purple-500/20 text-purple-200"
                  : "border-white/10 bg-white/5 text-gray-300 hover:border-white/20 hover:text-white"
              }`}
            >
              {preset}
            </button>
          ))}
        </div>

        <input
          type="text"
          value={vendorPriority}
          onChange={(e) => setVendorPriority(e.target.value)}
          placeholder="Or type custom shift: e.g. Swap sit-down dinner for street food trucks and spend more on DJ..."
          className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:border-purple-500 focus:outline-none"
        />
      </div>

      {/* Error Message */}
      {error && (
        <div
          role="alert"
          className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-xs text-red-300"
        >
          ⚠️ {error}
        </div>
      )}

      {/* Diff View Showing Live Simulation Results */}
      {scenarioData && (
        <div className="space-y-6 pt-2" aria-live="polite">
          {/* Key Metric Diff Cards */}
          <div className="grid gap-4 sm:grid-cols-3">
            {/* Total Budget Diff */}
            <Card className="border-white/10 bg-white/[0.02]">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-400">
                Budget Variance
              </span>
              <div className="mt-2 flex items-baseline justify-between">
                <span className="text-2xl font-bold text-white">
                  ${Number(scenarioData.scenario_budget).toLocaleString()}
                </span>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                    scenarioData.budget_variance > 0
                      ? "bg-amber-500/20 text-amber-300"
                      : scenarioData.budget_variance < 0
                      ? "bg-emerald-500/20 text-emerald-300"
                      : "bg-gray-500/20 text-gray-300"
                  }`}
                >
                  {scenarioData.budget_variance >= 0
                    ? `+$${Number(scenarioData.budget_variance).toLocaleString()}`
                    : `-$${Math.abs(Number(scenarioData.budget_variance)).toLocaleString()}`}
                </span>
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Baseline: ${Number(scenarioData.baseline_budget).toLocaleString()}
              </p>
            </Card>

            {/* Guest Count Diff */}
            <Card className="border-white/10 bg-white/[0.02]">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-400">
                Guest Headcount Shift
              </span>
              <div className="mt-2 flex items-baseline justify-between">
                <span className="text-2xl font-bold text-white">
                  {scenarioData.scenario_guest_count} guests
                </span>
                <span className="rounded-full bg-indigo-500/20 px-2 py-0.5 text-xs font-semibold text-indigo-300">
                  {scenarioData.scenario_guest_count - scenarioData.baseline_guest_count >= 0
                    ? `+${scenarioData.scenario_guest_count - scenarioData.baseline_guest_count}`
                    : `${scenarioData.scenario_guest_count - scenarioData.baseline_guest_count}`}
                </span>
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Baseline: {scenarioData.baseline_guest_count} guests
              </p>
            </Card>

            {/* Cost Per Guest Diff */}
            <Card className="border-white/10 bg-white/[0.02]">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-400">
                Cost Per Guest
              </span>
              <div className="mt-2 flex items-baseline justify-between">
                <span className="text-2xl font-bold text-white">
                  ${Number(scenarioData.cost_per_guest_scenario).toFixed(2)}
                </span>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                    scenarioData.cost_per_guest_scenario > scenarioData.cost_per_guest_baseline
                      ? "bg-amber-500/20 text-amber-300"
                      : "bg-emerald-500/20 text-emerald-300"
                  }`}
                >
                  {scenarioData.cost_per_guest_scenario >= scenarioData.cost_per_guest_baseline
                    ? `+$${(scenarioData.cost_per_guest_scenario - scenarioData.cost_per_guest_baseline).toFixed(2)}`
                    : `-$${Math.abs(scenarioData.cost_per_guest_scenario - scenarioData.cost_per_guest_baseline).toFixed(2)}`}
                </span>
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Baseline: ${Number(scenarioData.cost_per_guest_baseline).toFixed(2)} / guest
              </p>
            </Card>
          </div>

          {/* AI Strategic Analysis Banner */}
          {scenarioData.analysis_summary && (
            <div className="rounded-xl border border-indigo-500/30 bg-indigo-500/10 p-4 text-xs leading-relaxed text-indigo-200">
              💡 <strong>Scenario Analysis:</strong> {scenarioData.analysis_summary}
            </div>
          )}

          {/* Category-by-Category Diff Reallocation Table */}
          <div className="overflow-hidden rounded-xl border border-white/10 bg-black/40">
            <div className="border-b border-white/10 bg-white/[0.03] px-6 py-3.5">
              <h3 className="text-sm font-bold text-white">
                📊 Category Reallocation Diff
              </h3>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-gray-300">
                <thead className="border-b border-white/5 bg-white/[0.02] text-gray-400">
                  <tr>
                    <th scope="col" className="px-6 py-3 font-semibold">Category</th>
                    <th scope="col" className="px-6 py-3 font-semibold">Simulated Amount</th>
                    <th scope="col" className="px-6 py-3 font-semibold">Allocation %</th>
                    <th scope="col" className="px-6 py-3 font-semibold">Variance vs. Current</th>
                    <th scope="col" className="px-6 py-3 font-semibold">Planning Notes</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {scenarioData.plan.items.map((item, idx) => {
                    const catKey = item.category.toLowerCase().trim();
                    const baselineAmt = baselineCategoryMap.get(catKey);
                    const hasBaseline = baselineAmt !== undefined;
                    const diff = hasBaseline ? Number(item.allocated_amount) - baselineAmt : 0;

                    return (
                      <tr key={idx} className="transition-colors hover:bg-white/[0.02]">
                        <td className="px-6 py-3 font-semibold text-white">
                          {item.category}
                        </td>
                        <td className="px-6 py-3 font-mono font-medium text-white">
                          ${Number(item.allocated_amount).toLocaleString()}
                        </td>
                        <td className="px-6 py-3">
                          <div className="flex items-center gap-2">
                            <span className="w-9 font-mono text-gray-400">
                              {item.percentage}%
                            </span>
                            <div className="h-1.5 w-16 overflow-hidden rounded-full bg-white/10">
                              <div
                                className="h-full rounded-full bg-indigo-500"
                                style={{ width: `${Math.min(item.percentage, 100)}%` }}
                              />
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-3 font-mono">
                          {hasBaseline ? (
                            <span
                              className={`font-semibold ${
                                diff > 0
                                  ? "text-amber-400"
                                  : diff < 0
                                  ? "text-emerald-400"
                                  : "text-gray-400"
                              }`}
                            >
                              {diff > 0
                                ? `+$${diff.toLocaleString()}`
                                : diff < 0
                                ? `-$${Math.abs(diff).toLocaleString()}`
                                : "$0"}
                            </span>
                          ) : (
                            <span className="text-gray-500">—</span>
                          )}
                        </td>
                        <td className="px-6 py-3 text-gray-400">
                          {item.notes || "—"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
