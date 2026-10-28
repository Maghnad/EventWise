import Link from "next/link";
import React from "react";

/* ==========================================================================
   Lightweight SVG Icons (No external dependencies, crisp 1.75px stroke)
   ========================================================================== */

function SparklesIcon({
  className = "h-4 w-4",
}: {
  className?: string;
}): React.JSX.Element {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3L12 3Z" />
      <path d="M5 3v4" />
      <path d="M19 17v4" />
      <path d="M3 5h4" />
      <path d="M17 19h4" />
    </svg>
  );
}

function ArrowRightIcon({
  className = "h-4 w-4",
}: {
  className?: string;
}): React.JSX.Element {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M5 12h14" />
      <path d="m12 5 7 7-7 7" />
    </svg>
  );
}

function CalculatorIcon({
  className = "h-5 w-5",
}: {
  className?: string;
}): React.JSX.Element {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <rect width="16" height="20" x="4" y="2" rx="2" />
      <line x1="8" x2="16" y1="6" y2="6" />
      <line x1="16" x2="16" y1="14" y2="18" />
      <path d="M16 10h.01" />
      <path d="M12 10h.01" />
      <path d="M8 10h.01" />
      <path d="M12 14h.01" />
      <path d="M8 14h.01" />
      <path d="M12 18h.01" />
      <path d="M8 18h.01" />
    </svg>
  );
}

function CalendarDaysIcon({
  className = "h-5 w-5",
}: {
  className?: string;
}): React.JSX.Element {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <rect width="18" height="18" x="3" y="4" rx="2" />
      <line x1="16" x2="16" y1="2" y2="6" />
      <line x1="8" x2="8" y1="2" y2="6" />
      <line x1="3" x2="21" y1="10" y2="10" />
      <path d="M8 14h.01" />
      <path d="M12 14h.01" />
      <path d="M16 14h.01" />
      <path d="M8 18h.01" />
      <path d="M12 18h.01" />
      <path d="M16 18h.01" />
    </svg>
  );
}

function CheckSquareIcon({
  className = "h-5 w-5",
}: {
  className?: string;
}): React.JSX.Element {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="m9 11 3 3L22 4" />
      <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
    </svg>
  );
}

function UsersIcon({ className = "h-5 w-5" }: { className?: string }): React.JSX.Element {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}

function CheckIcon({ className = "h-4 w-4" }: { className?: string }): React.JSX.Element {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M20 6 9 17l-5-5" />
    </svg>
  );
}

/* ==========================================================================
   Feature & Step Data
   ========================================================================== */

const CORE_FEATURES = [
  {
    icon: CalculatorIcon,
    title: "Predictive Budget Ledger",
    description:
      "Automated line-item partitioning across venue, catering, and production with real-time what-if variance modeling.",
  },
  {
    icon: CalendarDaysIcon,
    title: "Critical-Path Timelines",
    description:
      "Backward-scheduled milestone tracking with dependency ordering, lead-time warnings, and run-of-show synchronization.",
  },
  {
    icon: CheckSquareIcon,
    title: "Vendor RFP & Scope Tracking",
    description:
      "Curated supplier categories, auto-generated interview questionnaires, and day-of operational checklists.",
  },
  {
    icon: UsersIcon,
    title: "Digital RSVP & AI FAQ Concierge",
    description:
      "Frictionless guest response links paired with an autonomous 24/7 assistant answering venue logistics in real-time.",
  },
];

const WORKFLOW_STEPS = [
  {
    step: "01",
    title: "Define Parameters",
    description:
      "Input event type, headcount, target date, and preliminary budget in under two minutes.",
  },
  {
    step: "02",
    title: "Synthesize Operating Plan",
    description:
      "Autonomous multi-agent intelligence generates an itemized ledger, milestone schedule, and RFP questionnaires.",
  },
  {
    step: "03",
    title: "Refine & Execute",
    description:
      "Adjust allocations, simulate guest variance, manage invitations, and run the show with total clarity.",
  },
];

/* ==========================================================================
   Main Landing Page Component
   ========================================================================== */

export default function HomePage(): React.JSX.Element {
  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 selection:bg-indigo-600 selection:text-white">
      {/* ── 1. Sticky Minimal Navbar ────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 w-full border-b border-zinc-800/80 bg-[#09090b]/90 backdrop-blur-sm">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          {/* Logo */}
          <Link href="/" className="group flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-900 text-indigo-400 transition-colors group-hover:border-zinc-700">
              <SparklesIcon className="h-4 w-4 text-indigo-400" />
            </div>
            <span className="text-base font-semibold tracking-tight text-zinc-100">
              EventWise
            </span>
          </Link>

          {/* Navigation Links */}
          <nav
            aria-label="Main Navigation"
            className="hidden items-center gap-8 text-sm font-medium text-zinc-400 md:flex"
          >
            <a href="#features" className="transition-colors hover:text-zinc-100">
              Features
            </a>
            <a href="#how-it-works" className="transition-colors hover:text-zinc-100">
              How it works
            </a>
            <a href="#preview" className="transition-colors hover:text-zinc-100">
              Platform
            </a>
            <Link href="/dashboard" className="transition-colors hover:text-zinc-100">
              Dashboard
            </Link>
          </nav>

          {/* Action CTAs */}
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="rounded-lg px-3.5 py-1.5 text-sm font-medium text-zinc-300 transition-colors hover:text-white"
            >
              Sign in
            </Link>
            <Link
              href="/signup"
              className="inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-indigo-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950"
            >
              Get started
            </Link>
          </div>
        </div>
      </header>

      <main id="main-content">
        {/* ── 2. Hero Section ─────────────────────────────────────────────────── */}
        <section className="mx-auto max-w-6xl px-6 pb-16 pt-20 text-center sm:pb-24 sm:pt-28">
          {/* Eyebrow Label */}
          <div className="inline-flex items-center gap-2 rounded-md border border-zinc-800 bg-zinc-900/80 px-3 py-1 text-xs font-medium text-zinc-300">
            <span className="flex h-1.5 w-1.5 rounded-full bg-indigo-500" />
            <span>AI-Powered Event Planning</span>
          </div>

          {/* Large Headline */}
          <h1 className="mx-auto mt-6 max-w-4xl text-balance text-4xl font-bold tracking-tight text-zinc-100 sm:text-6xl sm:leading-[1.1]">
            Plan unforgettable events, without the chaos.
          </h1>

          {/* One-Line Subheadline */}
          <p className="mx-auto mt-5 max-w-2xl text-balance text-base text-zinc-400 sm:text-lg sm:leading-relaxed">
            An intelligent workspace for event directors and teams — orchestrating
            budgets, milestone schedules, vendor scopes, and guest RSVPs with precision.
          </p>

          {/* Action CTAs */}
          <div className="mt-8 flex flex-col items-center justify-center gap-3.5 sm:flex-row">
            <Link
              href="/signup"
              className="inline-flex h-11 w-full items-center justify-center rounded-lg bg-indigo-600 px-6 text-sm font-medium text-white shadow-sm transition-colors hover:bg-indigo-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950 sm:w-auto"
            >
              <span>Start planning free</span>
              <ArrowRightIcon className="ml-2 h-4 w-4" />
            </Link>
            <a
              href="#how-it-works"
              className="inline-flex h-11 w-full items-center justify-center rounded-lg border border-zinc-800 bg-zinc-900/60 px-5 text-sm font-medium text-zinc-300 transition-colors hover:bg-zinc-800 hover:text-white sm:w-auto"
            >
              See how it works
            </a>
          </div>

          {/* ── Product Preview / Mockup (Linear / Stripe Editorial Aesthetic) ─ */}
          <div id="preview" className="mt-16 text-left sm:mt-20">
            <div className="overflow-hidden rounded-xl border border-zinc-800 bg-[#121214] shadow-2xl shadow-black/80">
              {/* Window Chrome Header */}
              <div className="flex h-11 items-center justify-between border-b border-zinc-800/80 bg-zinc-900/60 px-4">
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded-full bg-zinc-700/80" />
                  <span className="h-3 w-3 rounded-full bg-zinc-700/80" />
                  <span className="h-3 w-3 rounded-full bg-zinc-700/80" />
                </div>
                <div className="flex items-center gap-2 text-xs font-medium text-zinc-400">
                  <span className="rounded bg-zinc-800/80 px-2.5 py-0.5 text-zinc-300">
                    Napa Valley Harvest Summit 2026
                  </span>
                  <span className="hidden rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-400 sm:inline-block">
                    Planning Active
                  </span>
                </div>
                <div className="font-mono text-xs text-zinc-500">Live Workspace</div>
              </div>

              {/* Mockup Dashboard Content */}
              <div className="p-6 sm:p-8">
                {/* Metrics Row */}
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  {/* Metric 1 */}
                  <div className="rounded-lg border border-zinc-800/80 bg-zinc-900/50 p-4">
                    <div className="flex items-center justify-between text-xs text-zinc-400">
                      <span>Total Budget</span>
                      <span className="font-mono font-medium text-emerald-400">
                        68% Allocated
                      </span>
                    </div>
                    <div className="mt-2 text-2xl font-bold tracking-tight text-zinc-100">
                      $45,000.00
                    </div>
                    <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-zinc-800">
                      <div className="h-full w-[68%] rounded-full bg-indigo-500" />
                    </div>
                    <div className="mt-2 text-[11px] text-zinc-500">
                      $14,400.00 contingency reserve remaining
                    </div>
                  </div>

                  {/* Metric 2 */}
                  <div className="rounded-lg border border-zinc-800/80 bg-zinc-900/50 p-4">
                    <div className="flex items-center justify-between text-xs text-zinc-400">
                      <span>Timeline Health</span>
                      <span className="font-mono font-medium text-indigo-400">
                        14 of 18 Complete
                      </span>
                    </div>
                    <div className="mt-2 text-2xl font-bold tracking-tight text-zinc-100">
                      78% On Track
                    </div>
                    <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-zinc-800">
                      <div className="h-full w-[78%] rounded-full bg-indigo-500" />
                    </div>
                    <div className="mt-2 text-[11px] text-zinc-500">
                      Next milestone: Finalize AV Run-of-Show in 3 days
                    </div>
                  </div>

                  {/* Metric 3 */}
                  <div className="rounded-lg border border-zinc-800/80 bg-zinc-900/50 p-4">
                    <div className="flex items-center justify-between text-xs text-zinc-400">
                      <span>Confirmed RSVPs</span>
                      <span className="font-mono font-medium text-emerald-400">
                        92% Response
                      </span>
                    </div>
                    <div className="mt-2 text-2xl font-bold tracking-tight text-zinc-100">
                      142 / 150
                    </div>
                    <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-zinc-800">
                      <div className="h-full w-[92%] rounded-full bg-emerald-500" />
                    </div>
                    <div className="mt-2 text-[11px] text-zinc-500">
                      8 dietary requests tagged for catering
                    </div>
                  </div>
                </div>

                {/* Sub-Panel: AI Plan Synthesis & Active Tasks */}
                <div className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-3">
                  {/* AI Concierge Summary */}
                  <div className="rounded-lg border border-zinc-800/80 bg-zinc-900/30 p-4 lg:col-span-2">
                    <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-indigo-400">
                      <SparklesIcon className="h-3.5 w-3.5" />
                      <span>Synthesized Operating Strategy</span>
                    </div>
                    <p className="mt-2 text-xs leading-relaxed text-zinc-300">
                      Autonomous budget allocation confirmed with standard 15% catering
                      variance. Floral and audio-visual contracts reviewed with customized
                      RFP clauses applied. RSVP concierge FAQ bot answered 34 venue
                      parking and transit questions.
                    </p>
                  </div>

                  {/* Operational Status */}
                  <div className="flex flex-col justify-between rounded-lg border border-zinc-800/80 bg-zinc-900/30 p-4">
                    <div className="text-xs font-medium text-zinc-400">
                      System Readiness
                    </div>
                    <div className="mt-1 flex items-center gap-2 text-xs font-medium text-zinc-200">
                      <CheckIcon className="h-4 w-4 text-emerald-400" />
                      <span>All 5 vendor scopes locked</span>
                    </div>
                    <div className="mt-1 flex items-center gap-2 text-xs font-medium text-zinc-200">
                      <CheckIcon className="h-4 w-4 text-emerald-400" />
                      <span>Zero budget overruns projected</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── 3. Subtle Social Proof Strip ────────────────────────────────────── */}
        <section
          aria-label="Social Proof"
          className="border-y border-zinc-800/80 bg-zinc-900/20 py-8"
        >
          <div className="mx-auto max-w-6xl px-6 text-center">
            <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
              Trusted by independent planners, agency directors, and enterprise teams
            </p>
            <div className="mt-5 flex flex-wrap items-center justify-center gap-x-12 gap-y-3 text-xs font-semibold tracking-wider text-zinc-400 sm:text-sm">
              <span>✦ KINETIK FORUM</span>
              <span>✦ MERIDIAN SUMMITS</span>
              <span>✦ STUDIO FOUNDRY</span>
              <span>✦ PACIFIC CREATIVE</span>
              <span>✦ AVENUE AGENCY</span>
            </div>
          </div>
        </section>

        {/* ── 4. Features Section ─────────────────────────────────────────────── */}
        <section
          id="features"
          aria-labelledby="features-heading"
          className="py-20 sm:py-28"
        >
          <div className="mx-auto max-w-6xl px-6">
            <div className="text-left sm:text-center">
              <h2
                id="features-heading"
                className="text-xs font-semibold uppercase tracking-wider text-indigo-400"
              >
                Core Capabilities
              </h2>
              <p className="mt-2 text-3xl font-bold tracking-tight text-zinc-100 sm:text-4xl">
                Everything required to orchestrate flawless events
              </p>
              <p className="mx-auto mt-3 max-w-2xl text-sm text-zinc-400 sm:text-base">
                Replace disconnected spreadsheets, email threads, and loose notes with an
                integrated operating system.
              </p>
            </div>

            <div className="mt-14 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {CORE_FEATURES.map((feature) => {
                const Icon = feature.icon;
                return (
                  <div
                    key={feature.title}
                    className="group rounded-xl border border-zinc-800 bg-zinc-900/40 p-6 transition-all duration-200 hover:-translate-y-0.5 hover:border-zinc-700"
                  >
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-900 text-indigo-400 transition-colors group-hover:border-zinc-700">
                      <Icon className="h-5 w-5" />
                    </div>
                    <h3 className="mt-4 text-base font-semibold text-zinc-100">
                      {feature.title}
                    </h3>
                    <p className="mt-2 text-sm leading-relaxed text-zinc-400">
                      {feature.description}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* ── 5. How It Works (3-Step Horizontal Flow) ────────────────────────── */}
        <section
          id="how-it-works"
          aria-labelledby="how-it-works-heading"
          className="border-t border-zinc-800/80 bg-zinc-900/10 py-20 sm:py-28"
        >
          <div className="mx-auto max-w-6xl px-6">
            <div className="text-left sm:text-center">
              <h2
                id="how-it-works-heading"
                className="text-xs font-semibold uppercase tracking-wider text-indigo-400"
              >
                Workflow
              </h2>
              <p className="mt-2 text-3xl font-bold tracking-tight text-zinc-100 sm:text-4xl">
                From concept to showtime in three steps
              </p>
              <p className="mx-auto mt-3 max-w-2xl text-sm text-zinc-400 sm:text-base">
                Coordinated intelligence turns broad visions into actionable execution
                plans.
              </p>
            </div>

            <div className="mt-14 grid grid-cols-1 gap-6 md:grid-cols-3">
              {WORKFLOW_STEPS.map((item) => (
                <div
                  key={item.step}
                  className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6"
                >
                  <div className="font-mono text-xs font-semibold tracking-wider text-indigo-400">
                    Step {item.step}
                  </div>
                  <h3 className="mt-3 text-lg font-semibold text-zinc-100">
                    {item.title}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-zinc-400">
                    {item.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── 6. Final CTA Section ────────────────────────────────────────────── */}
        <section className="py-20 sm:py-28">
          <div className="mx-auto max-w-6xl px-6">
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-10 text-center sm:p-14">
              <h2 className="text-2xl font-bold tracking-tight text-zinc-100 sm:text-3xl">
                Ready to plan your next event with total confidence?
              </h2>
              <p className="mx-auto mt-3 max-w-lg text-sm text-zinc-400 sm:text-base">
                Join forward-thinking event teams using EventWise to orchestrate seamless,
                stress-free experiences.
              </p>
              <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
                <Link
                  href="/signup"
                  className="inline-flex h-11 w-full items-center justify-center rounded-lg bg-indigo-600 px-6 text-sm font-medium text-white shadow-sm transition-colors hover:bg-indigo-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950 sm:w-auto"
                >
                  <span>Start planning free</span>
                  <ArrowRightIcon className="ml-2 h-4 w-4" />
                </Link>
                <Link
                  href="/dashboard"
                  className="inline-flex h-11 w-full items-center justify-center rounded-lg border border-zinc-800 bg-zinc-900 px-5 text-sm font-medium text-zinc-300 transition-colors hover:bg-zinc-800 hover:text-white sm:w-auto"
                >
                  Explore Dashboard
                </Link>
              </div>
              <p className="mt-4 text-xs text-zinc-500">
                No credit card required • Instant access to planning workspace
              </p>
            </div>
          </div>
        </section>
      </main>

      {/* ── 7. Minimal Footer ───────────────────────────────────────────────── */}
      <footer className="border-t border-zinc-800/80 bg-[#09090b] py-12 text-sm text-zinc-400">
        <div className="mx-auto max-w-6xl px-6">
          <div className="flex flex-col items-start justify-between gap-6 border-b border-zinc-800/60 pb-8 md:flex-row md:items-center">
            <div className="flex items-center gap-2.5">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-900 text-indigo-400">
                <SparklesIcon className="h-3.5 w-3.5" />
              </div>
              <span className="font-semibold text-zinc-100">EventWise</span>
              <span className="ml-2 text-xs text-zinc-500">
                Intelligent Event Orchestration
              </span>
            </div>
            <div className="flex flex-wrap gap-6 text-xs text-zinc-400">
              <Link href="/dashboard" className="transition-colors hover:text-zinc-100">
                Dashboard
              </Link>
              <Link href="/signup" className="transition-colors hover:text-zinc-100">
                Sign Up
              </Link>
              <Link href="/login" className="transition-colors hover:text-zinc-100">
                Sign In
              </Link>
              <a href="#features" className="transition-colors hover:text-zinc-100">
                Features
              </a>
              <a href="#how-it-works" className="transition-colors hover:text-zinc-100">
                How it works
              </a>
            </div>
          </div>
          <div className="flex flex-col items-center justify-between gap-4 pt-6 text-xs text-zinc-500 sm:flex-row">
            <p>© 2026 EventWise, Inc. All rights reserved.</p>
            <div className="flex gap-4">
              <span className="transition-colors hover:text-zinc-400">Privacy</span>
              <span className="transition-colors hover:text-zinc-400">Terms</span>
              <span className="transition-colors hover:text-zinc-400">Security</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
