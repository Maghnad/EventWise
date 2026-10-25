import type { Metadata } from "next";
import { LoginPage } from "@/features/auth";

export const metadata: Metadata = {
  title: "Sign In",
  description: "Sign in to your EventWise account.",
};

export default function Page(): React.JSX.Element {
  return <LoginPage />;
}
