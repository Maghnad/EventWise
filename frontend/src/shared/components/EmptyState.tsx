"use client";

import Link from "next/link";
import React from "react";
import { Button, Card } from "@/shared/components";

export interface EmptyStateProps {
  icon?: string | React.ReactNode;
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
  actionHref?: string;
  secondaryActionText?: string;
  secondaryActionHref?: string;
  className?: string;
}

export function EmptyState({
  icon = "🎈",
  title,
  description,
  actionText,
  onAction,
  actionHref,
  secondaryActionText,
  secondaryActionHref,
  className = "",
}: EmptyStateProps): React.JSX.Element {
  return (
    <Card
      role="region"
      aria-label={title}
      className={`rounded-2xl border-dashed border-white/15 bg-white/[0.02] p-8 sm:p-12 text-center backdrop-blur-sm ${className}`}
    >
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-500/10 text-3xl shadow-inner">
        {typeof icon === "string" ? <span>{icon}</span> : icon}
      </div>

      <h3 className="mt-4 text-lg font-bold text-white sm:text-xl">{title}</h3>
      <p className="mx-auto mt-2 max-w-md text-xs sm:text-sm text-gray-400 leading-relaxed">
        {description}
      </p>

      {(actionText || secondaryActionText) && (
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          {actionText && (
            actionHref ? (
              <Link href={actionHref}>
                <Button variant="primary" className="text-xs px-4 py-2">
                  {actionText}
                </Button>
              </Link>
            ) : (
              <Button
                variant="primary"
                onClick={onAction}
                className="text-xs px-4 py-2"
              >
                {actionText}
              </Button>
            )
          )}

          {secondaryActionText && secondaryActionHref && (
            <Link
              href={secondaryActionHref}
              className="inline-flex items-center justify-center rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold text-gray-300 transition-all hover:bg-white/10 hover:text-white"
            >
              {secondaryActionText}
            </Link>
          )}
        </div>
      )}
    </Card>
  );
}
