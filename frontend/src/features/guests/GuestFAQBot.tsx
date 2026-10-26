"use client";

import React, { useEffect, useRef, useState } from "react";
import { Button } from "@/shared/components";
import { askGuestFaq } from "./guestsApi";

export interface GuestFAQBotProps {
  eventId: string;
  eventTitle?: string;
  guestName?: string;
  className?: string;
  isFloating?: boolean;
}

interface FaqMessage {
  id: string;
  sender: "guest" | "bot";
  text: string;
  timestamp: string;
}

const DEFAULT_QUESTIONS = [
  "What is the dress code?",
  "Where is parking located?",
  "What time should I arrive?",
  "How are dietary restrictions handled?",
];

export function GuestFAQBot({
  eventId,
  eventTitle = "Event",
  guestName,
  className = "",
  isFloating = false,
}: GuestFAQBotProps): React.JSX.Element {
  const [isOpen, setIsOpen] = useState(!isFloating);
  const [messages, setMessages] = useState<FaqMessage[]>([
    {
      id: "bot-welcome",
      sender: "bot",
      text: `Hello${guestName ? ` ${guestName}` : ""}! I am the event assistant for ${eventTitle}. Have any questions about attire, schedule, parking, or accommodations? Just ask below!`,
      timestamp: "Just now",
    },
  ]);
  const [inputQuestion, setInputQuestion] = useState("");
  const [isAsking, setIsAsking] = useState(false);
  const [suggestedQuestions, setSuggestedQuestions] =
    useState<string[]>(DEFAULT_QUESTIONS);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen, isAsking]);

  const handleSend = async (qToSend?: string) => {
    const question = (qToSend ?? inputQuestion).trim();
    if (!question || isAsking) return;

    const userMsg: FaqMessage = {
      id: `guest-${Date.now()}`,
      sender: "guest",
      text: question,
      timestamp: new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!qToSend) setInputQuestion("");
    setIsAsking(true);

    try {
      const res = await askGuestFaq(eventId, {
        question,
        guest_name: guestName,
      });

      const botMsg: FaqMessage = {
        id: `bot-${Date.now()}`,
        sender: "bot",
        text: res.answer,
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      };

      setMessages((prev) => [...prev, botMsg]);
      if (res.suggested_questions && res.suggested_questions.length > 0) {
        setSuggestedQuestions(res.suggested_questions);
      }
    } catch {
      const fallbackMsg: FaqMessage = {
        id: `bot-${Date.now()}`,
        sender: "bot",
        text: `The event organizer will provide full details near the date. Feel free to leave a note on your RSVP for any custom requirements!`,
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      };
      setMessages((prev) => [...prev, fallbackMsg]);
    } finally {
      setIsAsking(false);
    }
  };

  const content = (
    <div
      className={`flex flex-col rounded-2xl border border-purple-500/20 bg-gradient-to-b from-gray-950/95 via-purple-950/30 to-black/95 shadow-2xl backdrop-blur-2xl ${
        isFloating ? "max-h-[500px] w-80 sm:w-96" : "w-full"
      }`}
    >
      {/* Bot Header */}
      <div className="flex items-center justify-between border-b border-white/10 bg-white/[0.02] px-4 py-3.5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-tr from-purple-600 to-indigo-600 text-sm shadow-md shadow-purple-500/20">
            💬
          </div>
          <div>
            <h3 className="text-xs font-bold text-white">Event FAQ Assistant</h3>
            <p className="text-[10px] text-gray-400">Ask any questions about the event</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-400">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
            Active
          </span>
          {isFloating && (
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="rounded-lg p-1 text-gray-400 transition-colors hover:bg-white/10 hover:text-white"
              aria-label="Close FAQ Assistant"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Suggested chips */}
      <div className="border-b border-white/5 bg-white/[0.01] px-4 py-2.5">
        <span className="mb-1.5 block text-[10px] font-semibold uppercase tracking-wider text-purple-300">
          Common Questions
        </span>
        <div className="flex flex-wrap gap-1.5">
          {suggestedQuestions.map((q, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleSend(q)}
              disabled={isAsking}
              className="rounded-full border border-purple-500/20 bg-purple-500/10 px-2.5 py-0.5 text-[11px] text-purple-200 transition-all hover:border-purple-400 hover:bg-purple-500/20 disabled:opacity-40"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Message Feed with aria-live */}
      <div
        role="log"
        aria-live="polite"
        aria-label="FAQ Conversation"
        className="max-h-[280px] min-h-[200px] flex-1 space-y-3 overflow-y-auto p-4"
      >
        {messages.map((msg) => {
          const isGuest = msg.sender === "guest";
          return (
            <div
              key={msg.id}
              className={`flex flex-col ${isGuest ? "items-end" : "items-start"}`}
            >
              <div className="mb-0.5 flex items-center gap-1.5 text-[10px] text-gray-400">
                <span className="font-semibold text-gray-300">
                  {isGuest ? guestName || "You" : "Event Bot"}
                </span>
                <span>•</span>
                <span>{msg.timestamp}</span>
              </div>

              <div
                className={`max-w-[85%] rounded-2xl px-3.5 py-2 text-xs leading-relaxed ${
                  isGuest
                    ? "rounded-br-xs bg-purple-600 text-white"
                    : "rounded-bl-xs border border-white/10 bg-white/[0.04] text-gray-200"
                }`}
              >
                <p className="whitespace-pre-line">{msg.text}</p>
              </div>
            </div>
          );
        })}

        {isAsking && (
          <div
            className="flex animate-pulse items-center gap-2 rounded-xl bg-purple-500/10 px-3 py-1.5 text-[11px] text-purple-300"
            aria-live="assertive"
          >
            <span className="h-1.5 w-1.5 animate-ping rounded-full bg-purple-400" />
            <span>Finding answer...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Question Input */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="flex items-center gap-2 rounded-b-2xl border-t border-white/10 bg-black/40 p-3"
      >
        <input
          type="text"
          value={inputQuestion}
          onChange={(e) => setInputQuestion(e.target.value)}
          placeholder="Ask a question about the event..."
          disabled={isAsking}
          className="flex-1 rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2 text-xs text-white placeholder-gray-500 transition-all focus:border-purple-500 focus:outline-none"
          aria-label="Type your question for the event host"
        />
        <Button
          type="submit"
          disabled={!inputQuestion.trim() || isAsking}
          className="bg-purple-600 px-3 py-2 text-xs hover:bg-purple-500"
          aria-label="Send question"
        >
          {isAsking ? "..." : "Ask →"}
        </Button>
      </form>
    </div>
  );

  if (isFloating) {
    return (
      <div className={`fixed bottom-6 right-6 z-50 ${className}`}>
        {isOpen ? (
          content
        ) : (
          <button
            type="button"
            onClick={() => setIsOpen(true)}
            className="flex items-center gap-2 rounded-full border border-purple-400/40 bg-gradient-to-r from-purple-600 to-indigo-600 px-4 py-3 text-xs font-bold text-white shadow-xl shadow-purple-900/40 transition-all hover:scale-105 hover:shadow-2xl"
            aria-label="Open Event FAQ Assistant"
          >
            <span className="text-base">💬</span>
            <span>Have Questions? Ask Bot</span>
          </button>
        )}
      </div>
    );
  }

  return <div className={className}>{content}</div>;
}
