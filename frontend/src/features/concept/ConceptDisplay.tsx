"use client";

import { useState } from "react";
import type { ColorSwatch, ConceptBoard } from "@/shared/contracts";
import { Button, Card } from "@/shared/components";

export interface ConceptDisplayProps {
  concept: ConceptBoard;
  onGenerateMoodboard?: () => void;
  isLoadingMoodboard?: boolean;
}

export function ConceptDisplay({
  concept,
  onGenerateMoodboard,
  isLoadingMoodboard = false,
}: ConceptDisplayProps): React.JSX.Element {
  const [copiedHex, setCopiedHex] = useState<string | null>(null);

  const handleCopyColor = (hex: string) => {
    navigator.clipboard.writeText(hex);
    setCopiedHex(hex);
    setTimeout(() => setCopiedHex(null), 2000);
  };

  return (
    <div className="space-y-8" aria-label="Aesthetic Concept Board">
      {/* Theme Header & Summary */}
      <section className="relative overflow-hidden rounded-2xl border border-indigo-500/30 bg-gradient-to-br from-indigo-950/40 via-purple-950/20 to-black/60 p-8 shadow-2xl backdrop-blur-xl">
        <div className="relative z-10 flex flex-col justify-between gap-6 md:flex-row md:items-center">
          <div className="max-w-2xl">
            <span className="inline-block rounded-full bg-indigo-500/20 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-indigo-300">
              Creative Theme
            </span>
            <h2 className="mt-2 text-3xl font-extrabold tracking-tight text-white md:text-4xl">
              {concept.theme_name}
            </h2>
            <p className="mt-3 text-base leading-relaxed text-gray-300">
              {concept.vibe_summary}
            </p>
          </div>

          {onGenerateMoodboard && (
            <div className="flex-shrink-0">
              <Button
                onClick={onGenerateMoodboard}
                disabled={isLoadingMoodboard}
                className="w-full shadow-lg shadow-indigo-500/20 md:w-auto"
              >
                {isLoadingMoodboard ? (
                  <span className="flex items-center gap-2">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    Generating Staging...
                  </span>
                ) : (
                  "🎨 Generate Spatial Moodboard →"
                )}
              </Button>
            </div>
          )}
        </div>
      </section>

      {/* 1. Color Palette */}
      <section aria-labelledby="palette-heading">
        <div className="mb-4 flex items-center justify-between">
          <h3
            id="palette-heading"
            className="text-lg font-bold tracking-tight text-white"
          >
            🎨 Curated Color Palette
          </h3>
          <span className="text-xs text-gray-400">Click hex to copy</span>
        </div>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
          {concept.color_palette.map((swatch: ColorSwatch) => (
            <Card
              key={swatch.hex_code}
              className="group cursor-pointer overflow-hidden p-0 transition-all hover:scale-[1.02] hover:border-indigo-500/50"
              onClick={() => handleCopyColor(swatch.hex_code)}
              role="button"
              tabIndex={0}
              aria-label={`Copy color ${swatch.name} hex code ${swatch.hex_code}`}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  handleCopyColor(swatch.hex_code);
                }
              }}
            >
              {/* Color swatch preview */}
              <div
                className="h-24 w-full transition-transform group-hover:scale-105"
                style={{ backgroundColor: swatch.hex_code }}
              />

              <div className="p-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold capitalize text-indigo-400">
                    {swatch.role}
                  </span>
                  <span className="font-mono text-[10px] text-gray-400">
                    {copiedHex === swatch.hex_code ? "✓ Copied" : swatch.hex_code}
                  </span>
                </div>
                <p className="mt-1 truncate text-xs font-medium text-white">
                  {swatch.name}
                </p>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* 2. Decor Motifs & Textures */}
      <section aria-labelledby="motifs-heading">
        <h3
          id="motifs-heading"
          className="mb-4 text-lg font-bold tracking-tight text-white"
        >
          🌿 Key Decor Motifs & Textures
        </h3>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {concept.decor_motifs.map((motif, index) => (
            <div
              key={index}
              className="flex items-start gap-3 rounded-xl border border-white/10 bg-white/[0.03] p-4 transition-all hover:border-indigo-500/30 hover:bg-white/[0.05]"
            >
              <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-indigo-500/10 text-xs font-bold text-indigo-400">
                #{index + 1}
              </div>
              <div>
                <p className="text-sm font-medium text-white">{motif}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 3. Spatial Layout Ideas */}
      <section aria-labelledby="layout-heading">
        <h3
          id="layout-heading"
          className="mb-4 text-lg font-bold tracking-tight text-white"
        >
          📐 Spatial Flow & Layout Ideas
        </h3>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {concept.layout_ideas.map((idea, index) => (
            <div
              key={index}
              className="rounded-xl border border-white/10 bg-gradient-to-b from-white/[0.04] to-transparent p-5 transition-all hover:border-purple-500/30 hover:bg-white/[0.06]"
            >
              <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-purple-300">
                Spatial Zone {index + 1}
              </div>
              <p className="text-sm leading-relaxed text-gray-200">{idea}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 4. High-Level Schedule */}
      <section aria-labelledby="schedule-heading">
        <h3
          id="schedule-heading"
          className="mb-4 text-lg font-bold tracking-tight text-white"
        >
          ⏰ High-Level Schedule & Milestones
        </h3>
        <div className="relative ml-3 space-y-6 border-l border-indigo-500/30 pl-6">
          {concept.high_level_schedule.map((milestone, idx) => (
            <div key={idx} className="group relative">
              {/* Dot */}
              <div className="absolute -left-[31px] top-1 h-3.5 w-3.5 rounded-full border-2 border-indigo-500 bg-black transition-all group-hover:scale-125 group-hover:bg-indigo-400" />

              <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4 transition-all hover:border-white/20 hover:bg-white/[0.05]">
                <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                  <span className="font-mono text-xs font-semibold text-indigo-400">
                    {milestone.phase}
                  </span>
                  <h4 className="text-sm font-bold text-white">{milestone.activity}</h4>
                </div>
                {milestone.description && (
                  <p className="mt-2 text-xs leading-normal text-gray-400">
                    {milestone.description}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
