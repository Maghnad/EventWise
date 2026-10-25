"use client";

import { useEffect, type ReactNode } from "react";
import { cn } from "@/shared/utils";

export interface ModalProps {
  /** Controls open/closed visibility. */
  isOpen: boolean;
  /** Callback invoked when dismissal is requested (Escape, backdrop, or close button). */
  onClose: () => void;
  /** Modal header title. */
  title: string;
  /** Optional secondary subtitle or instructions. */
  description?: string;
  /** Body contents. */
  children: ReactNode;
  /** Custom card container classes. */
  className?: string;
}

/**
 * Accessible dialog modal with backdrop blur, keyboard navigation (Escape), and focus isolation.
 */
export function Modal({
  isOpen,
  onClose,
  title,
  description,
  children,
  className,
}: ModalProps): React.JSX.Element | null {
  useEffect(() => {
    if (!isOpen) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      aria-describedby={description ? "modal-description" : undefined}
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/70 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal Window */}
      <div
        className={cn(
          "relative z-10 w-full max-w-lg rounded-2xl border border-white/10 bg-gray-900/95 p-6 shadow-2xl backdrop-blur-xl",
          className,
        )}
      >
        <div className="flex items-start justify-between">
          <div>
            <h2 id="modal-title" className="text-xl font-bold text-white">
              {title}
            </h2>
            {description && (
              <p id="modal-description" className="mt-1 text-sm text-gray-400">
                {description}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            className="rounded-lg p-1.5 text-gray-400 transition-colors hover:bg-white/10 hover:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <span aria-hidden="true" className="text-lg leading-none">
              &times;
            </span>
          </button>
        </div>

        <div className="mt-6">{children}</div>
      </div>
    </div>
  );
}
