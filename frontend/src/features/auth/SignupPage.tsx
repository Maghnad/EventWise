"use client";

import React, { useState } from "react";
import Link from "next/link";
import { z } from "zod";
import { Card } from "@/shared/components";
import type { ApiError } from "./authApi";
import { useAuth } from "./useAuth";

/* ==========================================================================
   Validation Schema
   ========================================================================== */

export const signupSchema = z.object({
  full_name: z.string().trim().min(2, "Full name must be at least 2 characters long"),
  email: z
    .string()
    .trim()
    .min(1, "Email address is required")
    .email("Please enter a valid email address"),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters long")
    .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
    .regex(/[0-9]/, "Password must contain at least one number"),
});

export type SignupFormData = z.infer<typeof signupSchema>;

/* ==========================================================================
   Component
   ========================================================================== */

export function SignupPage(): React.JSX.Element {
  const { signup } = useAuth();
  const [formData, setFormData] = useState<SignupFormData>({
    full_name: "",
    email: "",
    password: "",
  });
  const [fieldErrors, setFieldErrors] = useState<
    Partial<Record<keyof SignupFormData, string>>
  >({});
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear field-specific error as user types
    if (fieldErrors[name as keyof SignupFormData]) {
      setFieldErrors((prev) => ({ ...prev, [name]: undefined }));
    }
    if (globalError) setGlobalError(null);
  };

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    setGlobalError(null);

    const validation = signupSchema.safeParse(formData);
    if (!validation.success) {
      const errors: Partial<Record<keyof SignupFormData, string>> = {};
      validation.error.issues.forEach((issue) => {
        const fieldName = issue.path[0] as keyof SignupFormData;
        if (!errors[fieldName]) {
          errors[fieldName] = issue.message;
        }
      });
      setFieldErrors(errors);
      return;
    }

    setFieldErrors({});
    setIsSubmitting(true);

    try {
      await signup(validation.data);
    } catch (err) {
      const apiErr = err as ApiError;
      const message =
        typeof apiErr.detail === "object" &&
        apiErr.detail !== null &&
        "detail" in (apiErr.detail as Record<string, unknown>)
          ? String((apiErr.detail as Record<string, unknown>).detail)
          : apiErr.message || "Failed to create account. Please try again.";
      setGlobalError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main
      aria-label="Sign Up"
      className="flex min-h-screen items-center justify-center px-4 py-12 sm:px-6 lg:px-8"
    >
      <Card className="w-full max-w-md p-8 shadow-2xl">
        <header className="mb-8 text-center">
          <h1 className="gradient-text text-3xl font-extrabold tracking-tight">
            Create an Account
          </h1>
          <p className="mt-2 text-sm text-[var(--color-text-muted)]">
            Start planning intelligent events with your AI assistant.
          </p>
        </header>

        {/* Global Error Alert Banner */}
        {globalError && (
          <div
            role="alert"
            aria-live="polite"
            className="mb-6 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300"
          >
            <p>{globalError}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate className="space-y-6">
          {/* Full Name field */}
          <div>
            <label
              htmlFor="full_name"
              className="block text-sm font-medium text-[var(--color-text)]"
            >
              Full Name
            </label>
            <div className="mt-1">
              <input
                id="full_name"
                name="full_name"
                type="text"
                autoComplete="name"
                required
                value={formData.full_name}
                onChange={handleChange}
                aria-invalid={Boolean(fieldErrors.full_name)}
                aria-describedby={fieldErrors.full_name ? "name-error" : undefined}
                className="block w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder-gray-500 transition-colors focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Jane Doe"
              />
            </div>
            {fieldErrors.full_name && (
              <p
                id="name-error"
                role="alert"
                aria-live="polite"
                className="mt-1.5 text-xs text-red-400"
              >
                {fieldErrors.full_name}
              </p>
            )}
          </div>

          {/* Email field */}
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-[var(--color-text)]"
            >
              Email Address
            </label>
            <div className="mt-1">
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={formData.email}
                onChange={handleChange}
                aria-invalid={Boolean(fieldErrors.email)}
                aria-describedby={fieldErrors.email ? "email-error" : undefined}
                className="block w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder-gray-500 transition-colors focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="you@example.com"
              />
            </div>
            {fieldErrors.email && (
              <p
                id="email-error"
                role="alert"
                aria-live="polite"
                className="mt-1.5 text-xs text-red-400"
              >
                {fieldErrors.email}
              </p>
            )}
          </div>

          {/* Password field */}
          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-[var(--color-text)]"
            >
              Password
            </label>
            <div className="mt-1">
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="new-password"
                required
                value={formData.password}
                onChange={handleChange}
                aria-invalid={Boolean(fieldErrors.password)}
                aria-describedby={fieldErrors.password ? "password-error" : undefined}
                className="block w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder-gray-500 transition-colors focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="••••••••"
              />
            </div>
            {fieldErrors.password && (
              <p
                id="password-error"
                role="alert"
                aria-live="polite"
                className="mt-1.5 text-xs text-red-400"
              >
                {fieldErrors.password}
              </p>
            )}
          </div>

          {/* Submit button */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="flex w-full items-center justify-center rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? (
              <span className="flex items-center space-x-2">
                <span
                  aria-hidden="true"
                  className="h-4 w-4 animate-spin rounded-full border-2 border-white/20 border-t-white"
                />
                <span>Creating Account...</span>
              </span>
            ) : (
              "Create Account"
            )}
          </button>
        </form>

        <footer className="mt-6 text-center text-xs text-[var(--color-text-muted)]">
          Already have an account?{" "}
          <Link
            href="/login"
            className="font-medium text-indigo-400 underline-offset-4 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-500"
          >
            Sign in
          </Link>
        </footer>
      </Card>
    </main>
  );
}
