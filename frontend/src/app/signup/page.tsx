import type { Metadata } from "next";
import { SignupPage } from "@/features/auth";

export const metadata: Metadata = {
  title: "Create Account",
  description: "Sign up for an EventWise event planning account.",
};

export default function Page(): React.JSX.Element {
  return <SignupPage />;
}
