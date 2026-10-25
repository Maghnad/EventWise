/**
 * Utility to conditionally join CSS class names.
 *
 * @param classes - Class name strings, falsy values are filtered out
 * @returns       A single space-separated class string
 *
 * @example
 * ```ts
 * cn("px-4", isActive && "bg-blue-600", undefined) // "px-4 bg-blue-600"
 * ```
 */
export function cn(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(" ");
}

/**
 * Format an ISO date string into a human-readable locale string.
 *
 * @param iso     - ISO 8601 date string
 * @param locale  - BCP 47 locale tag (defaults to "en-US")
 * @returns       Formatted date string
 */
export function formatDate(iso: string, locale = "en-US"): string {
  return new Date(iso).toLocaleDateString(locale, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/**
 * Truncate a string and add an ellipsis if it exceeds `maxLength`.
 */
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength - 1) + "…";
}
