"use client";

import { useParams } from "next/navigation";
import { AuthGuard } from "@/features/auth";
import { TimelinePage } from "@/features/timeline";

export default function Page(): React.JSX.Element {
  const params = useParams<{ eventId: string }>();
  return (
    <AuthGuard>
      <main className="mx-auto max-w-7xl px-6 py-16">
        <TimelinePage eventId={params.eventId} />
      </main>
    </AuthGuard>
  );
}
