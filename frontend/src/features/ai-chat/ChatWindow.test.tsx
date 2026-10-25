import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { axe } from "jest-axe";
import { ChatWindow } from "./ChatWindow";
import * as aiChatApi from "./aiChatApi";

vi.mock("./aiChatApi", () => ({
  sendChatMessage: vi.fn(),
}));

describe("ChatWindow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders welcome message, title, and suggestion chips", () => {
    render(<ChatWindow />);

    expect(screen.getByText("AI Planning Concierge")).toBeInTheDocument();
    expect(
      screen.getByText(/Hello! I am your EventWise AI Concierge/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/💡 Quick Action Prompts/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: /How should I allocate a \$35,000 budget for 120 guests\?/i,
      }),
    ).toBeInTheDocument();
  });

  it("renders conversation messages with role and tool calls indicator", () => {
    const initialMessages = [
      {
        id: "msg-1",
        role: "user" as const,
        content: "What is my catering budget?",
        timestamp: "10:00 AM",
      },
      {
        id: "msg-2",
        role: "assistant" as const,
        content: "Your catering budget is estimated at $14,000.",
        timestamp: "10:01 AM",
        tool_calls_executed: [
          {
            tool_name: "calculate_budget",
            arguments: { total_budget: 35000 },
            result_summary: "Calculated catering 40%",
            status: "success" as const,
          },
        ],
      },
    ];

    render(<ChatWindow initialMessages={initialMessages} />);

    expect(screen.getByText("What is my catering budget?")).toBeInTheDocument();
    expect(
      screen.getByText("Your catering budget is estimated at $14,000."),
    ).toBeInTheDocument();
    expect(screen.getByText(/⚡ Domain Tools Executed \(1\)/i)).toBeInTheDocument();
    expect(screen.getByText("calculate_budget")).toBeInTheDocument();
  });

  it("submits a message through the input box and invokes API when eventId is provided", async () => {
    const user = userEvent.setup();
    const mockReply = {
      event_id: "evt-123",
      reply: "Based on your timeline, we need to book the venue now.",
      tool_calls_executed: [],
      suggested_actions: [],
    };
    vi.mocked(aiChatApi.sendChatMessage).mockResolvedValueOnce(mockReply);

    render(<ChatWindow eventId="evt-123" />);

    const input = screen.getByRole("textbox", {
      name: /message prompt to ai concierge/i,
    });
    const sendBtn = screen.getByRole("button", { name: /send message/i });

    await user.type(input, "When should I book the venue?");
    await user.click(sendBtn);

    expect(aiChatApi.sendChatMessage).toHaveBeenCalledWith("evt-123", {
      message: "When should I book the venue?",
      history: expect.any(Array),
    });

    await waitFor(() => {
      expect(
        screen.getByText("Based on your timeline, we need to book the venue now."),
      ).toBeInTheDocument();
    });
  });

  it("toggles tool argument details on button click", async () => {
    const user = userEvent.setup();
    const initialMessages = [
      {
        id: "msg-1",
        role: "assistant" as const,
        content: "Budget analyzed.",
        timestamp: "10:00 AM",
        tool_calls_executed: [
          {
            tool_name: "calculate_budget",
            arguments: { test_arg: 123 },
            result_summary: "Done",
            status: "success" as const,
          },
        ],
      },
    ];

    render(<ChatWindow initialMessages={initialMessages} />);

    const expandBtn = screen.getByRole("button", {
      name: /expand tool details for calculate_budget/i,
    });
    await user.click(expandBtn);

    expect(screen.getByText(/test_arg/i)).toBeInTheDocument();
  });

  it("passes jest-axe accessibility checks with no violations", async () => {
    const { container } = render(<ChatWindow />);

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
