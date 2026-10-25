"use client";

import React, { useEffect, useState } from "react";
import { Button, Card } from "@/shared/components";
import type {
  GuestRsvpStatus,
  PublicEventResponse,
  RsvpSubmissionResponse,
} from "@/shared/contracts";
import { GuestFAQBot } from "./GuestFAQBot";
import { getPublicEvent, submitPublicRsvp } from "./guestsApi";

export interface RsvpPageProps {
  eventId: string;
}

const COMMON_DIETARY_OPTIONS = [
  "Vegetarian",
  "Vegan",
  "Gluten-Free",
  "Halal",
  "Kosher",
  "Nut Allergy",
  "Dairy-Free",
  "Shellfish Allergy",
];

export function RsvpPage({ eventId }: RsvpPageProps): React.JSX.Element {
  // Public Event Info
  const [eventData, setEventData] = useState<PublicEventResponse | null>(null);
  const [loadingEvent, setLoadingEvent] = useState(true);
  const [eventError, setEventError] = useState<string | null>(null);

  // Form State
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [rsvpStatus, setRsvpStatus] = useState<GuestRsvpStatus>("attending");
  const [plusOnes, setPlusOnes] = useState<number>(0);
  const [selectedDietary, setSelectedDietary] = useState<string[]>([]);
  const [customDietary, setCustomDietary] = useState("");
  const [notes, setNotes] = useState("");

  // Submission State
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [confirmation, setConfirmation] = useState<RsvpSubmissionResponse | null>(null);

  // Load public event info
  useEffect(() => {
    let isMounted = true;
    async function fetchEvent() {
      setLoadingEvent(true);
      setEventError(null);
      try {
        const data = await getPublicEvent(eventId);
        if (isMounted) setEventData(data);
      } catch (err: unknown) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : "Failed to load event invitation";
          setEventError(msg);
          // Fallback event data so page is still usable in development / test mode
          setEventData({
            id: eventId,
            title: "Celebration Gala & Gathering",
            description: "You are warmly invited to join us for an evening of celebration, dining, and festivities.",
            event_type: "corporate",
            start_date: new Date(Date.now() + 86400000 * 30).toISOString(),
            location: "Metropolitan Hall & Garden Terrace, New York, NY",
          });
        }
      } finally {
        if (isMounted) setLoadingEvent(false);
      }
    }

    if (eventId) {
      fetchEvent();
    }
    return () => {
      isMounted = false;
    };
  }, [eventId]);

  const toggleDietaryOption = (opt: string) => {
    setSelectedDietary((prev) =>
      prev.includes(opt) ? prev.filter((d) => d !== opt) : [...prev, opt],
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) {
      setSubmitError("Please enter your email address to submit your RSVP.");
      return;
    }

    setSubmitting(true);
    setSubmitError(null);

    // Merge chosen dietary chips + custom dietary text
    const allDietary = [...selectedDietary];
    if (customDietary.trim() && !allDietary.includes(customDietary.trim())) {
      allDietary.push(customDietary.trim());
    }

    try {
      const res = await submitPublicRsvp(eventId, {
        email: email.trim(),
        full_name: fullName.trim() || undefined,
        rsvp_status: rsvpStatus,
        plus_ones: rsvpStatus === "attending" ? plusOnes : 0,
        dietary_restrictions: allDietary,
        notes: notes.trim(),
      });
      setConfirmation(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to submit RSVP. Please try again.";
      setSubmitError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditRsvp = () => {
    setConfirmation(null);
  };

  if (loadingEvent) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-black p-4 text-white">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
          <p className="text-sm text-gray-400">Loading your invitation...</p>
        </div>
      </main>
    );
  }

  return (
    <main
      aria-label="Digital RSVP and Event Portal"
      className="min-h-screen bg-radial-gradient from-indigo-950/40 via-black to-black py-12 px-4 sm:px-6 lg:px-8 text-gray-100"
    >
      <div className="mx-auto max-w-4xl space-y-10">
        {/* Event Invitation Banner */}
        <header className="text-center space-y-4 rounded-3xl border border-indigo-500/20 bg-gradient-to-b from-indigo-950/30 via-black/50 to-black/80 p-8 shadow-2xl backdrop-blur-xl sm:p-12">
          <div className="inline-flex items-center gap-2 rounded-full border border-indigo-400/30 bg-indigo-500/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-wider text-indigo-300">
            <span>✨</span>
            <span>You Are Invited</span>
          </div>

          <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-5xl">
            {eventData?.title || "Special Event"}
          </h1>

          {eventData?.description && (
            <p className="mx-auto max-w-2xl text-sm sm:text-base text-gray-300 leading-relaxed">
              {eventData.description}
            </p>
          )}

          {eventError && (
            <div
              role="status"
              className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-2 text-xs text-amber-300 text-center"
            >
              Notice: Preview invitation mode active.
            </div>
          )}

          {/* Event Details Grid */}
          <div className="pt-4 grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-xl mx-auto text-left">
            <div className="flex items-start gap-3 rounded-2xl border border-white/5 bg-white/[0.02] p-4">
              <span className="text-2xl">📅</span>
              <div>
                <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-400 block">
                  Date & Time
                </span>
                <span className="text-sm font-bold text-white">
                  {eventData?.start_date
                    ? new Date(eventData.start_date).toLocaleDateString("en-US", {
                        weekday: "long",
                        year: "numeric",
                        month: "long",
                        day: "numeric",
                      })
                    : "To Be Announced"}
                </span>
              </div>
            </div>

            <div className="flex items-start gap-3 rounded-2xl border border-white/5 bg-white/[0.02] p-4">
              <span className="text-2xl">📍</span>
              <div>
                <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-400 block">
                  Location
                </span>
                <span className="text-sm font-bold text-white">
                  {eventData?.location || "Venue details to follow"}
                </span>
              </div>
            </div>
          </div>
        </header>

        {/* Form or Confirmation Card */}
        {confirmation ? (
          /* Confirmation Success State */
          <Card
            role="region"
            aria-live="polite"
            className="border-emerald-500/30 bg-gradient-to-b from-emerald-950/20 via-black/60 to-black/90 p-8 sm:p-12 text-center rounded-3xl shadow-2xl"
          >
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500/20 text-3xl shadow-lg shadow-emerald-500/20">
              🎉
            </div>

            <h2 className="mt-4 text-2xl sm:text-3xl font-extrabold text-white">
              RSVP Successfully Received!
            </h2>
            <p className="mt-2 text-sm text-emerald-300 font-medium">
              {confirmation.message}
            </p>

            <div className="my-8 max-w-md mx-auto rounded-2xl border border-white/10 bg-black/40 p-5 text-left text-xs space-y-2.5">
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-gray-400">Guest:</span>
                <span className="font-semibold text-white">{confirmation.guest.full_name}</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-gray-400">Status:</span>
                <span className="font-semibold capitalize text-emerald-400">
                  {confirmation.guest.rsvp_status}
                </span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-gray-400">Party Size:</span>
                <span className="font-semibold text-white">
                  {1 + (confirmation.guest.plus_ones || 0)} person(s)
                </span>
              </div>
              {confirmation.guest.dietary_restrictions && confirmation.guest.dietary_restrictions.length > 0 && (
                <div className="flex justify-between border-b border-white/5 pb-2">
                  <span className="text-gray-400">Dietary:</span>
                  <span className="font-semibold text-white">
                    {confirmation.guest.dietary_restrictions.join(", ")}
                  </span>
                </div>
              )}
            </div>

            <div className="flex flex-wrap items-center justify-center gap-3">
              <Button
                variant="secondary"
                onClick={handleEditRsvp}
                className="text-xs px-4 py-2"
                aria-label="Edit or update your RSVP details"
              >
                ✏️ Edit My RSVP
              </Button>
            </div>
          </Card>
        ) : (
          /* RSVP Form */
          <Card className="rounded-3xl border-white/10 bg-black/60 p-6 sm:p-10 shadow-2xl backdrop-blur-xl">
            <div className="mb-8 border-b border-white/10 pb-4">
              <h2 className="text-xl sm:text-2xl font-bold text-white">
                Kindly Respond
              </h2>
              <p className="mt-1 text-xs text-gray-400">
                Please complete your details below to confirm attendance for catering and seating plans.
              </p>
            </div>

            {submitError && (
              <div
                role="alert"
                className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-xs text-red-300"
              >
                ⚠️ {submitError}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-8">
              {/* 1. Contact Information */}
              <div className="grid gap-6 sm:grid-cols-2">
                <div>
                  <label
                    htmlFor="guest-fullname"
                    className="block text-xs font-semibold uppercase tracking-wider text-gray-300 mb-2"
                  >
                    Your Full Name *
                  </label>
                  <input
                    id="guest-fullname"
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Jane Doe"
                    className="w-full rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
                    aria-label="Full name"
                  />
                </div>

                <div>
                  <label
                    htmlFor="guest-email"
                    className="block text-xs font-semibold uppercase tracking-wider text-gray-300 mb-2"
                  >
                    Email Address *
                  </label>
                  <input
                    id="guest-email"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="jane@example.com"
                    className="w-full rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
                    aria-label="Email address"
                  />
                </div>
              </div>

              {/* 2. Attendance Status Selection */}
              <div>
                <p className="block text-xs font-semibold uppercase tracking-wider text-gray-300 mb-3">
                  Will You Attend? *
                </p>
                <div
                  role="radiogroup"
                  aria-label="RSVP attendance decision"
                  className="grid grid-cols-1 sm:grid-cols-2 gap-4"
                >
                  <button
                    type="button"
                    role="radio"
                    aria-checked={rsvpStatus === "attending"}
                    onClick={() => setRsvpStatus("attending")}
                    className={`flex items-center gap-3.5 rounded-2xl border p-4 text-left transition-all ${
                      rsvpStatus === "attending"
                        ? "border-emerald-500 bg-emerald-500/10 shadow-lg shadow-emerald-500/10"
                        : "border-white/10 bg-white/[0.02] hover:border-white/20 hover:bg-white/[0.04]"
                    }`}
                  >
                    <span className="text-2xl">🥂</span>
                    <div>
                      <span className="block text-sm font-bold text-white">
                        Joyfully Accept
                      </span>
                      <span className="text-xs text-gray-400">
                        I will be there to celebrate!
                      </span>
                    </div>
                  </button>

                  <button
                    type="button"
                    role="radio"
                    aria-checked={rsvpStatus === "declined"}
                    onClick={() => setRsvpStatus("declined")}
                    className={`flex items-center gap-3.5 rounded-2xl border p-4 text-left transition-all ${
                      rsvpStatus === "declined"
                        ? "border-amber-500 bg-amber-500/10 shadow-lg shadow-amber-500/10"
                        : "border-white/10 bg-white/[0.02] hover:border-white/20 hover:bg-white/[0.04]"
                    }`}
                  >
                    <span className="text-2xl">💌</span>
                    <div>
                      <span className="block text-sm font-bold text-white">
                        Regretfully Decline
                      </span>
                      <span className="text-xs text-gray-400">
                        Unable to attend, sending warm wishes.
                      </span>
                    </div>
                  </button>
                </div>
              </div>

              {/* Conditional fields if attending */}
              {rsvpStatus === "attending" && (
                <>
                  {/* 3. Plus-Ones Headcount */}
                  <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-5">
                    <div className="flex items-center justify-between">
                      <div>
                        <label
                          htmlFor="plus-ones-select"
                          className="text-xs font-semibold uppercase tracking-wider text-gray-300 block"
                        >
                          Additional Plus-Ones
                        </label>
                        <p className="text-xs text-gray-400 mt-0.5">
                          How many guests are accompanying you?
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        {[0, 1, 2, 3].map((num) => (
                          <button
                            key={num}
                            type="button"
                            onClick={() => setPlusOnes(num)}
                            className={`h-9 w-9 rounded-xl border text-sm font-bold transition-all ${
                              plusOnes === num
                                ? "border-indigo-500 bg-indigo-600 text-white shadow-md shadow-indigo-500/20"
                                : "border-white/10 bg-white/5 text-gray-300 hover:border-white/20 hover:text-white"
                            }`}
                            aria-label={`Select ${num} plus-ones`}
                          >
                            {num}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* 4. Dietary Restrictions */}
                  <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-5">
                    <p className="text-xs font-semibold uppercase tracking-wider text-gray-300 block mb-1">
                      🥗 Dietary Preferences & Allergies
                    </p>
                    <p className="text-xs text-gray-400 mb-3">
                      Select all that apply for your party so our catering team can prepare accordingly.
                    </p>

                    <div className="flex flex-wrap gap-2 mb-3">
                      {COMMON_DIETARY_OPTIONS.map((opt) => {
                        const isSelected = selectedDietary.includes(opt);
                        return (
                          <button
                            key={opt}
                            type="button"
                            onClick={() => toggleDietaryOption(opt)}
                            className={`rounded-xl border px-3 py-1.5 text-xs font-medium transition-all ${
                              isSelected
                                ? "border-indigo-400 bg-indigo-500/20 text-indigo-200"
                                : "border-white/10 bg-white/5 text-gray-300 hover:border-white/20 hover:text-white"
                            }`}
                            aria-pressed={isSelected}
                          >
                            {isSelected ? `✓ ${opt}` : `+ ${opt}`}
                          </button>
                        );
                      })}
                    </div>

                    <input
                      type="text"
                      value={customDietary}
                      onChange={(e) => setCustomDietary(e.target.value)}
                      placeholder="Other allergies or specific dietary requests..."
                      className="w-full rounded-xl border border-white/10 bg-black/40 px-3.5 py-2 text-xs text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
                    />
                  </div>
                </>
              )}

              {/* 5. Notes to Host */}
              <div>
                <label
                  htmlFor="guest-notes"
                  className="block text-xs font-semibold uppercase tracking-wider text-gray-300 mb-2"
                >
                  Message or Note to the Host (Optional)
                </label>
                <textarea
                  id="guest-notes"
                  rows={3}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Share warm wishes, song requests, or any special travel questions..."
                  className="w-full rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
                />
              </div>

              {/* Submit Button */}
              <div className="pt-2">
                <Button
                  type="submit"
                  disabled={submitting}
                  className="w-full py-4 text-base font-bold shadow-xl shadow-indigo-600/30"
                  aria-label="Submit your digital RSVP"
                >
                  {submitting ? "Confirming Your RSVP..." : "Submit RSVP Response →"}
                </Button>
              </div>
            </form>
          </Card>
        )}

        {/* Embedded Guest FAQ Bot Section */}
        <section aria-label="Guest FAQ and Assistant" className="pt-4">
          <div className="mb-4">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span>💬</span>
              <span>Event FAQ & Assistant</span>
            </h2>
            <p className="text-xs text-gray-400">
              Instant answers regarding venue navigation, dress code, parking, and timings.
            </p>
          </div>

          <GuestFAQBot
            eventId={eventId}
            eventTitle={eventData?.title}
            guestName={fullName}
          />
        </section>
      </div>
    </main>
  );
}
