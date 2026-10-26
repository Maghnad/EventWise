import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "jest-axe";
import { TimelineView } from "./TimelineView";
import type { TimelineOverviewResponse } from "@/shared/contracts";

const mockOverview: TimelineOverviewResponse = {
  event_id: "evt-123",
  total_tasks: 3,
  completed_tasks: 1,
  tasks: [
    {
      id: "task-1",
      event_id: "evt-123",
      title: "Confirm Venue Deposit",
      description: "Transfer 50% advance for booking confirmation",
      start_time: "2026-11-01T10:00:00Z",
      end_time: "2026-11-01T12:00:00Z",
      status: "completed",
      category: "venue",
      order_index: 0,
      assigned_to: "Alice",
      created_at: "2026-10-24T12:00:00Z",
      updated_at: "2026-10-24T12:00:00Z",
    },
    {
      id: "task-2",
      event_id: "evt-123",
      title: "Finalize Catering Menu",
      description: "Tasting session with chef",
      start_time: "2026-11-10T14:00:00Z",
      end_time: "2026-11-10T16:00:00Z",
      status: "in_progress",
      category: "catering",
      order_index: 1,
      assigned_to: "Bob",
      created_at: "2026-10-24T12:00:00Z",
      updated_at: "2026-10-24T12:00:00Z",
    },
  ],
};

describe("TimelineView Component", () => {
  it("renders summary statistics and progress bar", () => {
    render(<TimelineView overview={mockOverview} />);

    expect(screen.getByText(/total tasks/i)).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("33%")).toBeInTheDocument();

    const progress = screen.getByRole("progressbar", {
      name: /timeline progress percentage/i,
    });
    expect(progress).toHaveAttribute("aria-valuenow", "33");
  });

  it("renders all task items and metadata", () => {
    render(<TimelineView overview={mockOverview} />);

    expect(screen.getByText("Confirm Venue Deposit")).toBeInTheDocument();
    expect(screen.getByText("Finalize Catering Menu")).toBeInTheDocument();
    expect(screen.getByText("completed")).toBeInTheDocument();
    expect(screen.getByText("in progress")).toBeInTheDocument();
  });

  it("handles status toggle, edit and delete callbacks", async () => {
    const user = userEvent.setup();
    const handleToggle = vi.fn();
    const handleEdit = vi.fn();
    const handleDelete = vi.fn();

    render(
      <TimelineView
        overview={mockOverview}
        onStatusToggle={handleToggle}
        onEditTask={handleEdit}
        onDeleteTask={handleDelete}
      />,
    );

    const toggleBtn = screen.getByRole("button", {
      name: /toggle task status for confirm venue deposit/i,
    });
    await user.click(toggleBtn);
    expect(handleToggle).toHaveBeenCalledWith(mockOverview.tasks[0]);

    const editBtn = screen.getByRole("button", { name: /edit confirm venue deposit/i });
    await user.click(editBtn);
    expect(handleEdit).toHaveBeenCalledWith(mockOverview.tasks[0]);

    const deleteBtn = screen.getByRole("button", {
      name: /delete confirm venue deposit/i,
    });
    await user.click(deleteBtn);
    expect(handleDelete).toHaveBeenCalledWith("task-1");
  });

  it("has no accessibility violations (jest-axe)", async () => {
    const { container } = render(<TimelineView overview={mockOverview} />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
