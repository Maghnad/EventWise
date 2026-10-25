"use client";

import { AuthGuard } from "@/features/auth";
import { AiChatPage } from "@/features/ai-chat";

export default function Page(): React.JSX.Element {
  return (
    <AuthGuard>
      <main className="mx-auto max-w-5xl px-6 py-16">
        <AiChatPage />
      </main>
    </AuthGuard>
  );
}
