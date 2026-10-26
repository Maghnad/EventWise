"use client";

import Link from "next/link";
import React from "react";
import { ChatWindow } from "./ChatWindow";

export function AiChatPage(): React.JSX.Element {
  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Link
              href="/dashboard"
              className="text-xs font-medium text-indigo-400 transition-colors hover:text-indigo-300"
            >
              ← Dashboard
            </Link>
          </div>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">
            ✨ AI Planning Assistant
          </h1>
          <p className="text-sm text-gray-400">
            Ask for budget allocations, milestone timelines, checklist ideas, and vendor
            advice.
          </p>
        </div>
      </div>

      {/* Main ChatWindow */}
      <ChatWindow
        title="EventWise Planning Concierge"
        subtitle="Multi-turn conversational planner with real-time domain tool execution."
      />
    </div>
  );
}
