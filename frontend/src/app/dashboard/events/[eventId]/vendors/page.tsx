"use client";

import { useParams } from "next/navigation";
import { AuthGuard } from "@/features/auth";
import { VendorsPage } from "@/features/vendors";

export default function Page(): React.JSX.Element {
  const params = useParams<{ eventId: string }>();
  return (
    <AuthGuard>
      <main className="mx-auto max-w-7xl px-6 py-16">
        <VendorsPage eventId={params.eventId} />
      </main>
    </AuthGuard>
  );
}
