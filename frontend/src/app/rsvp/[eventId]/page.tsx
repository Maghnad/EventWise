import type { Metadata } from "next";
import { RsvpPage } from "@/features/guests";

export const metadata: Metadata = {
  title: "Digital RSVP & Event Invitation | EventWise",
  description: "Respond to your event invitation and ask questions to the event concierge.",
};

interface PageProps {
  params: {
    eventId: string;
  };
}

export default function Page({ params }: PageProps) {
  return <RsvpPage eventId={params.eventId} />;
}
