"use client";

import { useParams } from "next/navigation";
import { AuthGuard } from "@/features/auth";
import { GuestsPage } from "@/features/guests";

export default function Page(): React.JSX.Element {
  const params = useParams<{ eventId: string }>();
  return (
    <AuthGuard>
      <main className="mx-auto max-w-7xl px-6 py-16">
        <GuestsPage eventId={params.eventId} />
      </main>
    </AuthGuard>
  );
}
