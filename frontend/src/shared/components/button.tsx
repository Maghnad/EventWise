import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/shared/utils";

/** Variant styling map for the Button component. */
const variants = {
  primary: "bg-indigo-600 text-white hover:bg-indigo-500 focus-visible:ring-indigo-500",
  secondary:
    "bg-white/10 text-white border border-white/20 hover:bg-white/20 focus-visible:ring-white/40",
  ghost: "bg-transparent text-gray-300 hover:bg-white/10 focus-visible:ring-white/30",
  danger: "bg-red-600 text-white hover:bg-red-500 focus-visible:ring-red-500",
} as const;

type Variant = keyof typeof variants;

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Visual variant of the button. */
  variant?: Variant;
}

/**
 * Reusable button component with predefined variants.
 *
 * @example
 * ```tsx
 * <Button variant="primary" onClick={handleSave}>Save</Button>
 * ```
 */
export function Button({
  variant = "primary",
  className,
  children,
  ...props
}: ButtonProps): React.JSX.Element {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900",
        "disabled:pointer-events-none disabled:opacity-50",
        variants[variant],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
