import Link from "next/link";
import React from "react";
import { Button, Card } from "@/shared/components";

const FEATURES = [
  {
    icon: "🎉",
    title: "Event Command Center",
    description:
      "Create, categorize, and organize your events with full lifecycle tracking from concept to completion.",
  },
  {
    icon: "💰",
    title: "Smart Budget Tracking",
    description:
      "Itemized allocations, paid deposits, vendor expenses, and real-time remaining budget calculations.",
  },
  {
    icon: "⏳",
    title: "Timeline & Milestones",
    description:
      "Schedule deliverables, task deadlines, and day-of run-of-show with integrated progress indicators.",
  },
  {
    icon: "🤝",
    title: "Vendor Management",
    description:
      "Organize service suppliers, track quotes and contracts, and verify day-of operational checklists.",
  },
  {
    icon: "👥",
    title: "Guest & RSVP Portal",
    description:
      "Manage invitations, real-time RSVP responses, plus-ones, and track dietary restriction preferences.",
  },
  {
    icon: "✨",
    title: "AI Planning Assistant",
    description:
      "Get instant recommendations for budget formulas, milestone schedules, and vendor interview tips.",
  },
];

export default function HomePage(): React.JSX.Element {
  return (
    <div className="relative min-h-screen bg-[#0b0d17] text-white selection:bg-indigo-500 selection:text-white">
      {/* Background ambient lighting */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -top-40 left-1/2 h-[600px] w-[900px] -translate-x-1/2 rounded-full bg-indigo-600/20 blur-[140px]"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute right-0 top-[600px] h-[450px] w-[600px] rounded-full bg-purple-600/10 blur-[130px]"
      />

      {/* Navigation Bar */}
      <header className="relative z-10 border-b border-white/10 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-2xl">✨</span>
            <span className="text-xl font-bold tracking-tight text-white">EventWise</span>
          </Link>
          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost" className="text-xs sm:text-sm">
                Sign In
              </Button>
            </Link>
            <Link href="/signup">
              <Button
                variant="primary"
                className="text-xs shadow-lg shadow-indigo-500/25 sm:text-sm"
              >
                Get Started Free
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="relative z-10 mx-auto max-w-7xl px-6 pb-24 pt-20 text-center sm:pb-32 sm:pt-28">
        <div className="mx-auto inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-4 py-1.5 text-xs font-medium text-indigo-300 backdrop-blur-md">
          <span>🚀</span>
          <span>Next-Gen Event Planning Powered by AI</span>
        </div>

        <h1 className="mt-8 text-balance text-4xl font-extrabold tracking-tight sm:text-6xl md:text-7xl">
          Effortless Event Planning, <br />
          <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            From Vision to Execution.
          </span>
        </h1>

        <p className="mx-auto mt-6 max-w-2xl text-balance text-base text-gray-300 sm:text-lg">
          Coordinate budgets, milestones, vendor checklists, and guest RSVPs seamlessly in
          one unified glassmorphic workspace with intelligent AI assistance.
        </p>

        {/* Call to Actions */}
        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <Link href="/signup">
            <Button
              variant="primary"
              className="px-8 py-3.5 text-sm font-semibold shadow-xl shadow-indigo-600/30 hover:shadow-indigo-600/50"
            >
              Start Planning Free →
            </Button>
          </Link>
          <Link href="/dashboard">
            <Button
              variant="secondary"
              className="border-white/20 bg-white/5 px-8 py-3.5 text-sm font-semibold hover:bg-white/10"
            >
              Explore Dashboard
            </Button>
          </Link>
        </div>

        {/* Feature Grid */}
        <section className="mt-28" aria-labelledby="features-heading">
          <div className="text-center">
            <h2
              id="features-heading"
              className="text-xs font-semibold uppercase tracking-wider text-indigo-400"
            >
              Complete Planning Suite
            </h2>
            <p className="mt-2 text-2xl font-bold tracking-tight text-white sm:text-3xl">
              Everything you need to orchestrate flawless events
            </p>
          </div>

          <div className="mt-12 grid gap-6 text-left sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((feature) => (
              <Card
                key={feature.title}
                className="group border border-white/10 bg-white/[0.03] p-6 transition-all duration-300 hover:-translate-y-1 hover:border-indigo-500/40 hover:bg-white/[0.07] hover:shadow-xl hover:shadow-indigo-500/10"
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-2xl transition-transform group-hover:scale-110">
                  {feature.icon}
                </div>
                <h3 className="mt-4 text-lg font-semibold text-white transition-colors group-hover:text-indigo-300">
                  {feature.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-gray-400">
                  {feature.description}
                </p>
              </Card>
            ))}
          </div>
        </section>

        {/* Footer CTA */}
        <div className="mt-28 rounded-3xl border border-white/10 bg-gradient-to-b from-white/[0.08] to-white/[0.02] p-10 backdrop-blur-md sm:p-14">
          <h2 className="text-2xl font-bold text-white sm:text-4xl">
            Ready to bring your next event to life?
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-sm text-gray-300">
            Sign up in seconds and start managing your events, budgets, and guests with
            modern precision.
          </p>
          <div className="mt-8 flex justify-center gap-4">
            <Link href="/signup">
              <Button variant="primary" className="px-8 py-3 text-sm">
                Get Started Free
              </Button>
            </Link>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/10 py-8 text-center text-xs text-gray-500">
        <p>© 2026 EventWise. All rights reserved.</p>
      </footer>
    </div>
  );
}
