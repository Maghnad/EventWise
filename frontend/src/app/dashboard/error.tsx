"use client";

import { useEffect } from "react";
import { Button, Card } from "@/shared/components";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Dashboard error caught by route error boundary:", error);
  }, [error]);

  return (
    <main className="mx-auto max-w-xl px-4 py-20">
      <Card
        role="alert"
        aria-live="assertive"
        className="rounded-3xl border border-red-500/30 bg-gradient-to-b from-red-950/20 via-black/80 to-black p-8 text-center shadow-2xl backdrop-blur-xl sm:p-10"
      >
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-red-500/20 text-3xl shadow-lg shadow-red-500/20">
          ⚠️
        </div>

        <h1 className="mt-4 text-2xl font-bold tracking-tight text-white">
          Dashboard Unavailable
        </h1>

        <p className="mt-2 text-xs leading-relaxed text-gray-400 sm:text-sm">
          {error.message || "An unexpected error occurred while loading your dashboard."}
        </p>

        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          <Button
            variant="primary"
            onClick={() => reset()}
            className="px-4 py-2 text-xs"
            aria-label="Retry loading dashboard"
          >
            🔄 Retry
          </Button>

          <a
            href="/dashboard"
            className="inline-flex items-center justify-center rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold text-white transition-all hover:border-white/20 hover:bg-white/10"
          >
            Refresh Page
          </a>
        </div>
      </Card>
    </main>
  );
}
