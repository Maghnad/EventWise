import React from "react";

export default function DashboardLoading(): React.JSX.Element {
  return (
    <div
      role="status"
      aria-label="Loading dashboard"
      className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12 space-y-10 animate-pulse"
    >
      {/* Header skeleton */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="space-y-2">
          <div className="h-8 w-48 rounded-xl bg-white/10" />
          <div className="h-4 w-72 rounded-lg bg-white/5" />
        </div>
        <div className="h-10 w-36 rounded-xl bg-white/10" />
      </div>

      {/* Stats row skeleton */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-24 rounded-2xl border border-white/5 bg-white/[0.02] p-5 space-y-2">
            <div className="h-3 w-20 rounded bg-white/10" />
            <div className="h-6 w-32 rounded bg-white/20" />
          </div>
        ))}
      </div>

      {/* Events section skeleton */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="h-6 w-36 rounded bg-white/10" />
          <div className="h-4 w-20 rounded bg-white/5" />
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-72 rounded-3xl border border-white/10 bg-white/[0.03] p-6 space-y-4"
            >
              <div className="flex justify-between items-center">
                <div className="h-5 w-16 rounded-full bg-white/10" />
                <div className="h-4 w-20 rounded bg-white/10" />
              </div>
              <div className="h-6 w-3/4 rounded bg-white/20" />
              <div className="h-4 w-full rounded bg-white/5" />

              {/* Progress bars skeleton */}
              <div className="space-y-3 pt-3">
                <div className="space-y-1">
                  <div className="h-3 w-28 rounded bg-white/10" />
                  <div className="h-2 w-full rounded-full bg-white/5" />
                </div>
                <div className="space-y-1">
                  <div className="h-3 w-28 rounded bg-white/10" />
                  <div className="h-2 w-full rounded-full bg-white/5" />
                </div>
                <div className="space-y-1">
                  <div className="h-3 w-28 rounded bg-white/10" />
                  <div className="h-2 w-full rounded-full bg-white/5" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
