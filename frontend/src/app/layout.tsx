import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { AuthProvider } from "@/features/auth";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "EventWise — AI Event Planning",
    template: "%s | EventWise",
  },
  description:
    "Plan unforgettable events with AI-powered suggestions, budgeting, timeline management, and vendor coordination.",
  keywords: ["event planning", "AI assistant", "budget tracker", "timeline"],
};

/**
 * Root layout shared across every page.
 *
 * Applies the Inter font, global CSS, and HTML lang attribute.
 */
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>): React.JSX.Element {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen antialiased">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
