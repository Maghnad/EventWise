"use client";

import { useEffect } from "react";
import { Button, Card } from "@/shared/components";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Global application error:", error);
  }, [error]);

  return (
    <html lang="en">
      <body className="min-h-screen bg-black text-white flex items-center justify-center p-4">
        <Card
          role="alert"
          aria-live="assertive"
          className="max-w-md w-full rounded-3xl border border-red-500/30 bg-gradient-to-b from-red-950/20 via-black to-black p-8 text-center shadow-2xl backdrop-blur-xl"
        >
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-red-500/20 text-3xl">
            ⚠️
          </div>

          <h1 className="mt-4 text-xl font-bold text-white">Application Error</h1>
          <p className="mt-2 text-xs text-gray-400">
            {error.message || "An unexpected system error occurred."}
          </p>

          <div className="mt-6 flex justify-center gap-3">
            <Button variant="primary" onClick={() => reset()} className="text-xs px-4 py-2">
              🔄 Try Again
            </Button>
            <a
              href="/"
              className="inline-flex items-center justify-center rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold text-white transition-all hover:bg-white/10"
            >
              Home
            </a>
          </div>
        </Card>
      </body>
    </html>
  );
}
