import type { Metadata } from "next";
import { AuthGuard } from "@/features/auth";
import { EventsPage } from "@/features/events";

export const metadata: Metadata = {
  title: "Events | EventWise",
  description: "Create, edit, and manage your events.",
};

export default function Page(): React.JSX.Element {
  return (
    <AuthGuard>
      <main className="mx-auto max-w-7xl px-6 py-16">
        <EventsPage />
      </main>
    </AuthGuard>
  );
}
