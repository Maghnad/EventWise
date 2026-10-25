"use client";

import { useState } from "react";
import { Button } from "@/shared/components";

export interface ConceptFormProps {
  onSubmit: (vibeBrief: string) => void;
  isLoading: boolean;
  defaultBrief?: string;
}

const INSPIRATION_CHIPS = [
  "Rustic-Chic Bohemian Sunset with Pampas Grass & Firepits",
  "Modern Minimalist Cyber-Gala with Neon Accents & Glass Tables",
  "Lush Botanical Garden Romance with Living Chandeliers & Moss",
  "Moody Victorian Candlelight Masquerade Ball",
  "Vibrant Mediterranean Coastal Fiesta with Terracotta & Citrus",
];

export function ConceptForm({
  onSubmit,
  isLoading,
  defaultBrief = "",
}: ConceptFormProps): React.JSX.Element {
  const [brief, setBrief] = useState(defaultBrief);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (brief.trim()) {
      onSubmit(brief.trim());
    }
  };

  const handleChipClick = (chipText: string) => {
    setBrief(chipText);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 shadow-2xl backdrop-blur-xl transition-all"
      aria-label="Event Concept Generation Form"
    >
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white">
            ✨ Design Creative Concept
          </h2>
          <p className="mt-1 text-xs text-gray-400">
            Describe the mood, sensory atmosphere, styling vision, or aesthetic keywords.
          </p>
        </div>
      </div>

      {/* Suggested Inspiration Chips */}
      <div className="mb-4">
        <span
          id="inspiration-chips-label"
          className="mb-2 block text-xs font-medium uppercase tracking-wider text-indigo-300/80"
        >
          Quick Inspiration
        </span>
        <div
          role="group"
          aria-labelledby="inspiration-chips-label"
          className="flex flex-wrap gap-2"
        >
          {INSPIRATION_CHIPS.map((chip) => (
            <button
              key={chip}
              type="button"
              onClick={() => handleChipClick(chip)}
              className="rounded-full border border-indigo-500/20 bg-indigo-500/10 px-3 py-1 text-xs text-indigo-300 transition-all hover:border-indigo-400 hover:bg-indigo-500/20 focus:outline-none focus:ring-2 focus:ring-indigo-400"
            >
              + {chip}
            </button>
          ))}
        </div>
      </div>

      {/* Vibe Brief Textarea */}
      <div className="mb-5">
        <label
          htmlFor="vibe-brief"
          className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-gray-300"
        >
          Vibe Brief & Aesthetic Vision
        </label>
        <textarea
          id="vibe-brief"
          rows={4}
          value={brief}
          onChange={(e) => setBrief(e.target.value)}
          placeholder="e.g. An intimate sunset celebration blending warm terracotta pottery, neutral linen runners, warm amber festoon lighting, and acoustic folk music..."
          className="w-full resize-y rounded-xl border border-white/10 bg-black/40 p-4 text-sm text-white placeholder-gray-500 transition-all focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
          required
          aria-required="true"
        />
      </div>

      {/* Actions */}
      <div className="flex flex-col items-center justify-between gap-3 sm:flex-row">
        <span className="text-xs text-gray-500">
          Powered by GPT-4o creative directorship
        </span>
        <Button
          type="submit"
          disabled={isLoading || !brief.trim()}
          className="w-full sm:w-auto"
        >
          {isLoading ? (
            <span className="flex items-center gap-2">
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              Crafting Concept...
            </span>
          ) : (
            "✨ Generate Concept Board"
          )}
        </Button>
      </div>
    </form>
  );
}
