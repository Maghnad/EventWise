"use client";

import React, { useEffect, useRef, useState } from "react";
import { Button } from "@/shared/components";
import type { ToolExecutionRecord } from "@/shared/contracts";
import { sendChatMessage } from "./aiChatApi";

export interface ChatMessageItem {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  tool_calls_executed?: ToolExecutionRecord[];
}

export interface ChatWindowProps {
  eventId?: string;
  initialMessages?: ChatMessageItem[];
  className?: string;
  title?: string;
  subtitle?: string;
}

const DEFAULT_SUGGESTIONS = [
  "How should I allocate a $35,000 budget for 120 guests?",
  "Draft milestone timeline tasks for 3 months before event",
  "Checklist of essential questions for catering & venue vendors",
  "Recommend 5 creative cocktail hour ideas and entertainment",
];

const INITIAL_WELCOME: ChatMessageItem = {
  id: "welcome-1",
  role: "assistant",
  content:
    "Hello! I am your EventWise AI Concierge. I can dynamically calculate budgets, generate milestone timelines, review vendor requirements, and refine your concept boards. How can I assist with your planning today?",
  timestamp: "Just now",
};

export function ChatWindow({
  eventId,
  initialMessages,
  className = "",
  title = "AI Planning Concierge",
  subtitle = "Multi-turn assistant equipped with domain tools for budget, timeline, and vendors.",
}: ChatWindowProps): React.JSX.Element {
  const [messages, setMessages] = useState<ChatMessageItem[]>(
    initialMessages && initialMessages.length > 0 ? initialMessages : [INITIAL_WELCOME],
  );
  const [inputText, setInputText] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [activeToolName, setActiveToolName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedTools, setExpandedTools] = useState<Record<string, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView?.({ behavior: "smooth" });
  }, [messages, isTyping]);

  const toggleToolExpanded = (toolId: string) => {
    setExpandedTools((prev) => ({
      ...prev,
      [toolId]: !prev[toolId],
    }));
  };

  const handleSend = async (textToSend?: string) => {
    const message = (textToSend ?? inputText).trim();
    if (!message || isTyping) return;

    const userMessage: ChatMessageItem = {
      id: `user-${Date.now()}`,
      role: "user",
      content: message,
      timestamp: new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!textToSend) setInputText("");
    setError(null);
    setIsTyping(true);
    setActiveToolName(null);

    // Build history for backend
    const historyPayload = messages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    try {
      if (eventId) {
        // Live API call to backend /api/events/{eventId}/chat
        setActiveToolName("Analyzing request with AI Agent...");
        const res = await sendChatMessage(eventId, {
          message,
          history: historyPayload,
        });

        const assistantMessage: ChatMessageItem = {
          id: `ai-${Date.now()}`,
          role: "assistant",
          content: res.reply,
          timestamp: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
          tool_calls_executed: res.tool_calls_executed || [],
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        // Fallback simulation when no event ID is provided
        setActiveToolName("calculate_budget");
        await new Promise((resolve) => setTimeout(resolve, 800));

        const simulatedTools: ToolExecutionRecord[] = [
          {
            tool_name: "calculate_budget",
            arguments: { guest_count: 120, total_budget: 35000 },
            result_summary:
              "Allocated catering (40%), venue (25%), decor (15%), entertainment (10%), buffer (10%)",
            status: "success",
          },
        ];

        const fallbackReply =
          `I have calculated the allocations based on your event requirements. ` +
          `For 120 guests with a $35,000 target, I recommend reserving ~$14,000 for gourmet catering & bar service, ` +
          `~$8,750 for the venue rental, and ~$5,250 for floral/decor design. Would you like me to adjust this in your Budget tracker or generate vendor interview questions?`;

        const assistantMessage: ChatMessageItem = {
          id: `ai-${Date.now()}`,
          role: "assistant",
          content: fallbackReply,
          timestamp: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
          tool_calls_executed: simulatedTools,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to obtain AI response";
      setError(msg);
    } finally {
      setIsTyping(false);
      setActiveToolName(null);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <section
      aria-label="AI Event Planning Chat Window"
      className={`flex flex-col rounded-2xl border border-indigo-500/20 bg-gradient-to-b from-black/80 via-indigo-950/20 to-black/90 shadow-2xl backdrop-blur-xl ${className}`}
    >
      {/* Chat Header */}
      <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-lg shadow-lg shadow-indigo-500/20">
            🤖
          </div>
          <div>
            <h2 className="text-base font-bold text-white">{title}</h2>
            <p className="text-xs text-gray-400">{subtitle}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-[11px] font-semibold text-emerald-400">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
            Agent Ready
          </span>
        </div>
      </div>

      {/* Suggested Quick Prompts */}
      <div className="border-b border-white/5 bg-white/[0.01] px-6 py-3">
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-gray-400">
          💡 Quick Action Prompts
        </p>
        <div className="flex flex-wrap gap-2">
          {DEFAULT_SUGGESTIONS.map((suggestion, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleSend(suggestion)}
              disabled={isTyping}
              className="rounded-lg border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-indigo-200 transition-all hover:border-indigo-400 hover:bg-indigo-500/20 hover:text-white disabled:opacity-50"
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>

      {/* Messages Feed with aria-live */}
      <div
        role="log"
        aria-live="polite"
        aria-label="Conversation messages"
        className="max-h-[520px] min-h-[380px] flex-1 space-y-4 overflow-y-auto p-6"
      >
        {messages.map((message) => {
          const isUser = message.role === "user";

          return (
            <div
              key={message.id}
              className={`flex flex-col ${isUser ? "items-end" : "items-start"}`}
            >
              <div className="mb-1 flex items-center gap-2 text-[11px] text-gray-400">
                <span className="font-semibold text-gray-300">
                  {isUser ? "You" : "EventWise AI"}
                </span>
                <span>•</span>
                <span>{message.timestamp}</span>
              </div>

              {/* Message Bubble */}
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  isUser
                    ? "rounded-br-xs bg-gradient-to-r from-indigo-600 to-indigo-700 text-white shadow-md"
                    : "rounded-bl-xs border border-white/10 bg-white/[0.04] text-gray-100 shadow-sm"
                }`}
              >
                <p className="whitespace-pre-line">{message.content}</p>

                {/* Tool Execution Indicators */}
                {message.tool_calls_executed &&
                  message.tool_calls_executed.length > 0 && (
                    <div className="mt-3 space-y-2 border-t border-white/10 pt-2.5">
                      <span className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-indigo-300">
                        ⚡ Domain Tools Executed ({message.tool_calls_executed.length})
                      </span>

                      <div className="space-y-1.5">
                        {message.tool_calls_executed.map((tool, tIdx) => {
                          const toolKey = `${message.id}-tool-${tIdx}`;
                          const isExpanded = !!expandedTools[toolKey];

                          return (
                            <div
                              key={toolKey}
                              className="rounded-lg border border-indigo-500/30 bg-indigo-950/40 p-2.5 text-xs"
                            >
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <span className="text-sm">🔧</span>
                                  <span className="font-mono font-bold text-indigo-200">
                                    {tool.tool_name}
                                  </span>
                                  <span
                                    className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                                      tool.status === "success"
                                        ? "bg-emerald-500/20 text-emerald-300"
                                        : "bg-red-500/20 text-red-300"
                                    }`}
                                  >
                                    {tool.status}
                                  </span>
                                </div>

                                <button
                                  type="button"
                                  onClick={() => toggleToolExpanded(toolKey)}
                                  className="text-[11px] text-indigo-400 underline hover:text-indigo-200 focus:outline-none"
                                  aria-label={`${isExpanded ? "Collapse" : "Expand"} tool details for ${tool.tool_name}`}
                                >
                                  {isExpanded ? "Hide Details ▲" : "View Arguments ▼"}
                                </button>
                              </div>

                              <p className="mt-1 text-[11px] text-gray-300">
                                {tool.result_summary}
                              </p>

                              {/* Collapsible Arguments Inspector */}
                              {isExpanded && (
                                <div className="mt-2 overflow-x-auto rounded bg-black/60 p-2 font-mono text-[10px] text-gray-400">
                                  <pre>{JSON.stringify(tool.arguments, null, 2)}</pre>
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
              </div>
            </div>
          );
        })}

        {/* Live typing / tool invocation state */}
        {isTyping && (
          <div
            className="flex animate-pulse items-center gap-3 rounded-xl border border-indigo-500/20 bg-indigo-500/10 px-4 py-2.5 text-xs text-indigo-300"
            aria-live="assertive"
          >
            <div className="flex space-x-1">
              <span className="h-2 w-2 animate-bounce rounded-full bg-indigo-400" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-indigo-400 [animation-delay:0.2s]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-indigo-400 [animation-delay:0.4s]" />
            </div>
            <span>
              {activeToolName
                ? `Agent running: ${activeToolName}...`
                : "AI Concierge is generating your response..."}
            </span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error notification */}
      {error && (
        <div
          role="alert"
          className="mx-6 mb-3 flex items-center justify-between rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-300"
        >
          <span>⚠️ {error}</span>
          <Button
            variant="ghost"
            onClick={() => handleSend()}
            className="px-2 py-0.5 text-xs text-red-300 hover:text-white"
          >
            Retry
          </Button>
        </div>
      )}

      {/* Input Composer */}
      <div className="rounded-b-2xl border-t border-white/10 bg-black/40 p-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-3"
        >
          <input
            ref={inputRef}
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask AI concierge to calculate budget, build timeline, or recommend vendors..."
            disabled={isTyping}
            className="flex-1 rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white placeholder-gray-500 transition-all focus:border-indigo-500 focus:bg-black/60 focus:outline-none"
            aria-label="Message prompt to AI concierge"
          />

          <Button
            type="submit"
            disabled={!inputText.trim() || isTyping}
            className="px-5 py-3 text-sm font-semibold tracking-wide"
            aria-label="Send message"
          >
            {isTyping ? "Thinking..." : "Send →"}
          </Button>
        </form>
      </div>
    </section>
  );
}
