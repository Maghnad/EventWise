import type { InputHTMLAttributes } from "react";
import { forwardRef } from "react";
import { cn } from "@/shared/utils";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  /** Visible label text. */
  label?: string;
  /** Accessible error message. */
  error?: string;
  /** Subtle helper text under the input. */
  helperText?: string;
}

/**
 * Accessible text input with label, error feedback, and glassmorphic styling.
 */
export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, error, helperText, id, className, ...props },
  ref,
): React.JSX.Element {
  const inputId = id ?? (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);
  const errorId = inputId ? `${inputId}-error` : undefined;
  const helperId = inputId ? `${inputId}-helper` : undefined;

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={inputId}
          className="mb-1.5 block text-xs font-medium text-gray-300"
        >
          {label}
        </label>
      )}
      <input
        ref={ref}
        id={inputId}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? errorId : helperText ? helperId : undefined}
        className={cn(
          "w-full rounded-lg border border-white/20 bg-white/5 px-3.5 py-2 text-sm text-white placeholder-gray-400 backdrop-blur-md transition-colors",
          "focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500",
          "disabled:cursor-not-allowed disabled:opacity-50",
          error && "border-red-500 focus:border-red-500 focus:ring-red-500",
          className,
        )}
        {...props}
      />
      {error && (
        <p
          id={errorId}
          role="alert"
          aria-live="polite"
          className="mt-1 text-xs text-red-400"
        >
          {error}
        </p>
      )}
      {!error && helperText && (
        <p id={helperId} className="mt-1 text-xs text-gray-400">
          {helperText}
        </p>
      )}
    </div>
  );
});
