import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "jest-axe";
import { BudgetBreakdown } from "./BudgetBreakdown";
import type { BudgetOverviewResponse } from "@/shared/contracts";

const mockOverview: BudgetOverviewResponse = {
  event_id: "evt-123",
  total_budget: 50000,
  total_allocated: 45000,
  total_spent: 20000,
  remaining_budget: 30000,
  currency: "USD",
  items: [
    {
      id: "item-1",
      event_id: "evt-123",
      category: "Catering",
      name: "Plated 3-Course Dinner",
      estimated_cost: 15000,
      actual_cost: 14500,
      paid_amount: 5000,
      status: "deposit_paid",
      vendor_id: "v-1",
      notes: "Vegetarian and gluten free options included",
      created_at: "2026-10-24T12:00:00Z",
      updated_at: "2026-10-24T12:00:00Z",
    },
    {
      id: "item-2",
      event_id: "evt-123",
      category: "Venue",
      name: "Grand Ballroom Rental",
      estimated_cost: 18000,
      actual_cost: 18000,
      paid_amount: 18000,
      status: "paid",
      vendor_id: "v-2",
      notes: "Includes sound and lighting package",
      created_at: "2026-10-24T12:00:00Z",
      updated_at: "2026-10-24T12:00:00Z",
    },
  ],
};

describe("BudgetBreakdown Component", () => {
  it("renders summary cards with correct amounts", () => {
    render(<BudgetBreakdown overview={mockOverview} />);

    expect(screen.getByText(/total budget/i)).toBeInTheDocument();
    expect(screen.getByText("USD 50,000")).toBeInTheDocument();
    expect(screen.getByText("USD 45,000")).toBeInTheDocument();
    expect(screen.getByText("USD 20,000")).toBeInTheDocument();
    expect(screen.getByText("USD 30,000")).toBeInTheDocument();
  });

  it("renders progress bar with 40% usage", () => {
    render(<BudgetBreakdown overview={mockOverview} />);

    const progress = screen.getByRole("progressbar", { name: /budget usage/i });
    expect(progress).toHaveAttribute("aria-valuenow", "40");
  });

  it("renders itemized budget table", () => {
    render(<BudgetBreakdown overview={mockOverview} />);

    expect(screen.getByText("Plated 3-Course Dinner")).toBeInTheDocument();
    expect(screen.getByText("Grand Ballroom Rental")).toBeInTheDocument();
    expect(screen.getByText("deposit paid")).toBeInTheDocument();
    expect(screen.getByText("paid")).toBeInTheDocument();
  });

  it("calls onEditItem and onDeleteItem when action buttons clicked", async () => {
    const user = userEvent.setup();
    const handleEdit = vi.fn();
    const handleDelete = vi.fn();

    render(
      <BudgetBreakdown
        overview={mockOverview}
        onEditItem={handleEdit}
        onDeleteItem={handleDelete}
      />,
    );

    const editBtn = screen.getByRole("button", { name: /edit plated 3-course dinner/i });
    await user.click(editBtn);
    expect(handleEdit).toHaveBeenCalledWith(mockOverview.items[0]);

    const deleteBtn = screen.getByRole("button", {
      name: /delete plated 3-course dinner/i,
    });
    await user.click(deleteBtn);
    expect(handleDelete).toHaveBeenCalledWith("item-1");
  });

  it("has no accessibility violations (jest-axe)", async () => {
    const { container } = render(<BudgetBreakdown overview={mockOverview} />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
