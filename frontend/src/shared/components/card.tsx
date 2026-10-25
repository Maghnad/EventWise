import React from "react";
import { cn } from "@/shared/utils";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

/**
 * A glassmorphic card container used across dashboard panels.
 */
export function Card({ children, className, ...props }: CardProps): React.JSX.Element {
  return (
    <div
      className={cn(
        "rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-md",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}
