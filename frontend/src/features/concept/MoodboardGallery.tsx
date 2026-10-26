"use client";

import { useState } from "react";
import Image from "next/image";
import type {
  AIMoodboardResponse,
  DalleImagePrompt,
  SpatialDecorItem,
} from "@/shared/contracts";
import { Button, Card, Modal } from "@/shared/components";

export interface MoodboardGalleryProps {
  moodboard: AIMoodboardResponse;
}

// Fallback high-resolution architectural & event staging imagery by zone
const ZONE_FALLBACK_IMAGES: Record<string, string> = {
  entrance:
    "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=1200&q=80",
  ceremony:
    "https://images.unsplash.com/photo-1511285560929-80b456fea0bc?auto=format&fit=crop&w=1200&q=80",
  altar:
    "https://images.unsplash.com/photo-1511285560929-80b456fea0bc?auto=format&fit=crop&w=1200&q=80",
  dining:
    "https://images.unsplash.com/photo-1519225424982-f857e3f89078?auto=format&fit=crop&w=1200&q=80",
  tablescape:
    "https://images.unsplash.com/photo-1519225424982-f857e3f89078?auto=format&fit=crop&w=1200&q=80",
  lounge:
    "https://images.unsplash.com/photo-1544457070-4cd773b4d71e?auto=format&fit=crop&w=1200&q=80",
  bar: "https://images.unsplash.com/photo-1544457070-4cd773b4d71e?auto=format&fit=crop&w=1200&q=80",
  default:
    "https://images.unsplash.com/photo-1465495976277-4387d4b0b4c6?auto=format&fit=crop&w=1200&q=80",
};

function getZoneImageUrl(zone: string): string {
  const normalized = zone.toLowerCase();
  for (const [key, url] of Object.entries(ZONE_FALLBACK_IMAGES)) {
    if (normalized.includes(key)) {
      return url;
    }
  }
  return ZONE_FALLBACK_IMAGES.default;
}

export function MoodboardGallery({
  moodboard,
}: MoodboardGalleryProps): React.JSX.Element {
  const [selectedPrompt, setSelectedPrompt] = useState<DalleImagePrompt | null>(null);
  const [copiedPromptIndex, setCopiedPromptIndex] = useState<number | null>(null);

  const handleCopyPrompt = (promptText: string, index: number) => {
    navigator.clipboard.writeText(promptText);
    setCopiedPromptIndex(index);
    setTimeout(() => setCopiedPromptIndex(null), 2500);
  };

  return (
    <div className="space-y-10" aria-label="Spatial Moodboard & Visual Staging">
      {/* Header Banner */}
      <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-purple-400">
              Visual Staging & Moodboard
            </span>
            <h2 className="mt-1 text-2xl font-bold tracking-tight text-white">
              Spatial Decor & GenAI Concepts
            </h2>
            <p className="mt-2 text-sm text-gray-300">{moodboard.concept_summary}</p>
          </div>
          <div className="rounded-xl border border-purple-500/30 bg-purple-500/10 px-4 py-3 text-right">
            <span className="block text-[10px] font-semibold uppercase tracking-wider text-purple-300">
              Total Decor Budget
            </span>
            <span className="text-xl font-extrabold text-white">
              ${moodboard.total_decor_budget.toLocaleString()}
            </span>
          </div>
        </div>
      </section>

      {/* 1. Spatial Decor Breakdown by Zone */}
      <section aria-labelledby="spatial-decor-heading">
        <div className="mb-4 flex items-center justify-between">
          <h3
            id="spatial-decor-heading"
            className="text-lg font-bold tracking-tight text-white"
          >
            🏛️ Spatial Decor Plan by Zone
          </h3>
          <span className="text-xs text-gray-400">
            {moodboard.spatial_decor_list.length} Zones Styled
          </span>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {moodboard.spatial_decor_list.map((item: SpatialDecorItem, idx) => (
            <Card
              key={idx}
              className="flex flex-col justify-between border-white/10 bg-gradient-to-b from-white/[0.04] to-black/40 p-6 transition-all hover:border-indigo-500/30"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <h4 className="text-base font-bold text-white">{item.zone}</h4>
                  <span className="rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-emerald-400">
                    ${item.estimated_cost.toLocaleString()}
                  </span>
                </div>

                {/* Decor Elements */}
                <div className="mt-4">
                  <h5 className="text-[11px] font-semibold uppercase tracking-wider text-indigo-300">
                    Decor & Floral Elements
                  </h5>
                  <ul className="mt-2 space-y-1 text-xs text-gray-300">
                    {item.decor_elements.map((elem, i) => (
                      <li key={i} className="flex items-center gap-2">
                        <span className="text-indigo-400">•</span>
                        <span>{elem}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Lighting & Ambiance */}
                <div className="mt-4 rounded-lg border border-white/5 bg-black/30 p-3">
                  <h5 className="text-[11px] font-semibold uppercase tracking-wider text-purple-300">
                    Lighting & Ambiance
                  </h5>
                  <p className="mt-1 text-xs text-gray-300">
                    {item.lighting_and_ambiance}
                  </p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* 2. Visual Staging Image Gallery & GenAI Diffusion Prompts */}
      <section aria-labelledby="visual-prompts-heading">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h3
              id="visual-prompts-heading"
              className="text-lg font-bold tracking-tight text-white"
            >
              📸 GenAI Visual Staging & Diffusion Prompts
            </h3>
            <p className="mt-0.5 text-xs text-gray-400">
              Photorealistic visual concepts powered by generative AI. Click prompt to
              copy or view fullscreen.
            </p>
          </div>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {moodboard.image_prompts.map((imgPrompt: DalleImagePrompt, index) => {
            const imageUrl = getZoneImageUrl(imgPrompt.target_zone);

            return (
              <Card
                key={index}
                className="group flex flex-col justify-between overflow-hidden border-white/10 bg-black/40 p-0 transition-all hover:scale-[1.01] hover:border-purple-500/50 hover:shadow-2xl hover:shadow-purple-500/10"
              >
                {/* Visual Concept Image Container (Lazy-Loaded) */}
                <div className="relative aspect-[16/10] w-full overflow-hidden bg-neutral-900">
                  <Image
                    src={imageUrl}
                    alt={`Staging visual for ${imgPrompt.target_zone}`}
                    fill
                    unoptimized
                    sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                    className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />

                  {/* Target Zone Badge */}
                  <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between">
                    <span className="rounded-lg bg-black/60 px-2.5 py-1 text-xs font-semibold text-white backdrop-blur-md">
                      {imgPrompt.target_zone}
                    </span>
                    <span className="rounded-md bg-white/20 px-2 py-0.5 font-mono text-[10px] text-gray-200 backdrop-blur-md">
                      {imgPrompt.aspect_ratio}
                    </span>
                  </div>
                </div>

                {/* Prompt Details */}
                <div className="flex flex-1 flex-col justify-between p-4">
                  <div>
                    <p className="line-clamp-3 text-xs leading-relaxed text-gray-300">
                      &quot;{imgPrompt.prompt}&quot;
                    </p>

                    {imgPrompt.style_notes && (
                      <div className="mt-3 flex flex-wrap gap-1">
                        {imgPrompt.style_notes.split(",").map((tag, tIdx) => (
                          <span
                            key={tIdx}
                            className="rounded-full bg-white/5 px-2 py-0.5 text-[10px] text-gray-400"
                          >
                            {tag.trim()}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="mt-4 flex items-center gap-2 border-t border-white/5 pt-3">
                    <Button
                      variant="secondary"
                      className="flex-1 px-2.5 py-1.5 text-xs"
                      onClick={() => handleCopyPrompt(imgPrompt.prompt, index)}
                      aria-label="Copy GenAI prompt to clipboard"
                    >
                      {copiedPromptIndex === index ? "✓ Copied!" : "📋 Copy GenAI Prompt"}
                    </Button>
                    <Button
                      variant="ghost"
                      className="px-2 py-1.5 text-xs"
                      onClick={() => setSelectedPrompt(imgPrompt)}
                      aria-label="View prompt in full modal"
                    >
                      🔍
                    </Button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </section>

      {/* Fullscreen Prompt Inspection Modal */}
      {selectedPrompt && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedPrompt(null)}
          title={`GenAI Diffusion Prompt: ${selectedPrompt.target_zone}`}
        >
          <div className="space-y-4">
            <div className="relative aspect-video w-full overflow-hidden rounded-xl bg-neutral-900">
              <Image
                src={getZoneImageUrl(selectedPrompt.target_zone)}
                alt={selectedPrompt.target_zone}
                fill
                unoptimized
                className="h-full w-full object-cover"
              />
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                Full Generative AI Diffusion Prompt
              </p>
              <div className="mt-1 rounded-xl border border-white/10 bg-black/60 p-4 font-mono text-xs leading-relaxed text-gray-200">
                {selectedPrompt.prompt}
              </div>
            </div>

            <div className="flex items-center justify-between text-xs text-gray-400">
              <span>
                Aspect Ratio: <strong>{selectedPrompt.aspect_ratio}</strong>
              </span>
              {selectedPrompt.style_notes && (
                <span>
                  Style: <strong>{selectedPrompt.style_notes}</strong>
                </span>
              )}
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <Button variant="secondary" onClick={() => setSelectedPrompt(null)}>
                Close
              </Button>
              <Button
                onClick={() => {
                  navigator.clipboard.writeText(selectedPrompt.prompt);
                  setSelectedPrompt(null);
                }}
              >
                📋 Copy Prompt & Close
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
