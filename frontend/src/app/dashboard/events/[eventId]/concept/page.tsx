"use client";

import { useParams } from "next/navigation";
import { AuthGuard } from "@/features/auth";
import { ConceptPage } from "@/features/concept";

export default function Page(): React.JSX.Element {
  const params = useParams<{ eventId: string }>();

  return (
    <AuthGuard>
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        <ConceptPage eventId={params.eventId} />
      </main>
    </AuthGuard>
  );
}
