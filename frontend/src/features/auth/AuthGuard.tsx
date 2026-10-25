"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "./useAuth";

interface AuthGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

/**
 * Route protection wrapper component.
 *
 * Ensures the wrapped subtree is only rendered for authenticated users.
 * Redirects unauthenticated visitors to /login.
 */
export function AuthGuard({
  children,
  fallback,
}: AuthGuardProps): React.JSX.Element | null {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    if (fallback) {
      return <>{fallback}</>;
    }
    return (
      <div
        role="status"
        aria-live="polite"
        className="flex min-h-[60vh] flex-col items-center justify-center space-y-4"
      >
        <div
          aria-hidden="true"
          className="h-10 w-10 animate-spin rounded-full border-4 border-indigo-500/20 border-t-indigo-600"
        />
        <span className="text-sm text-[var(--color-text-muted)]">
          Verifying authorization...
        </span>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
