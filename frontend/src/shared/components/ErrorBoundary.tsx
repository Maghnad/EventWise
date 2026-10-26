"use client";

import React, { Component, type ErrorInfo, type ReactNode } from "react";
import { Button, Card } from "@/shared/components";

export interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onReset?: () => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error("ErrorBoundary caught an unhandled error:", error, errorInfo);
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <section
          role="alert"
          aria-live="assertive"
          className="mx-auto my-12 max-w-lg p-4"
        >
          <Card className="rounded-2xl border-red-500/30 bg-gradient-to-b from-red-950/20 via-black/80 to-black p-8 text-center shadow-2xl backdrop-blur-xl">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-red-500/20 text-3xl shadow-lg shadow-red-500/20">
              ⚠️
            </div>

            <h2 className="mt-4 text-xl font-bold tracking-tight text-white">
              Something went wrong
            </h2>

            <p className="mt-2 text-xs leading-relaxed text-gray-400">
              {this.state.error?.message ||
                "An unexpected rendering error occurred. Please try reloading the page or reset the component."}
            </p>

            <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
              <Button
                variant="secondary"
                onClick={this.handleReset}
                className="px-4 py-2 text-xs"
                aria-label="Try recovering from error"
              >
                🔄 Try Again
              </Button>
              <a
                href="/dashboard"
                className="inline-flex items-center justify-center rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold text-white transition-all hover:border-white/20 hover:bg-white/10"
              >
                ← Back to Dashboard
              </a>
            </div>
          </Card>
        </section>
      );
    }

    return this.props.children;
  }
}
