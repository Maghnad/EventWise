import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { axe } from "jest-axe";
import { VendorChecklist } from "./VendorChecklist";
import type { VendorChecklistResponse } from "@/shared/contracts";

const mockChecklist: VendorChecklistResponse = {
  event_id: "evt-123",
  total_items: 3,
  completed_items: 1,
  items: [
    {
      id: "item-1",
      event_id: "evt-123",
      vendor_category: "Catering",
      task_name: "Confirm tasting menu",
      is_completed: true,
      due_date: "2026-06-01",
      notes: "Vegetarian options required",
      assigned_vendor_id: "v-1",
      assigned_vendor_name: "Gourmet Catering Co.",
      created_at: "2026-01-01",
      updated_at: "2026-01-01",
    },
    {
      id: "item-2",
      event_id: "evt-123",
      vendor_category: "Catering",
      task_name: "Finalize drink pairings",
      is_completed: false,
      due_date: "2026-06-15",
      notes: "",
      assigned_vendor_id: "v-1",
      assigned_vendor_name: "Gourmet Catering Co.",
      created_at: "2026-01-01",
      updated_at: "2026-01-01",
    },
    {
      id: "item-3",
      event_id: "evt-123",
      vendor_category: "Photography",
      task_name: "Submit shot list",
      is_completed: false,
      due_date: "2026-07-01",
      notes: "Golden hour sunset photos",
      assigned_vendor_id: "v-2",
      assigned_vendor_name: "Shutter Studio",
      created_at: "2026-01-01",
      updated_at: "2026-01-01",
    },
  ],
};

describe("VendorChecklist", () => {
  it("renders summary statistics and progress bar correctly", () => {
    render(<VendorChecklist checklist={mockChecklist} />);

    expect(screen.getByText("Total Items")).toBeInTheDocument();
    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(screen.getByText("33%")).toBeInTheDocument();

    const progressBar = screen.getByRole("progressbar", {
      name: /vendor deliverables progress/i,
    });
    expect(progressBar).toHaveAttribute("aria-valuenow", "33");
  });

  it("groups deliverables by category and displays tasks", () => {
    render(<VendorChecklist checklist={mockChecklist} />);

    expect(screen.getByText(/Catering \(1\/2\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Photography \(0\/1\)/i)).toBeInTheDocument();
    expect(screen.getByText("Confirm tasting menu")).toBeInTheDocument();
    expect(screen.getByText("Submit shot list")).toBeInTheDocument();
  });

  it("calls onToggleComplete when checkbox button is clicked", async () => {
    const user = userEvent.setup();
    const handleToggle = vi.fn();

    render(<VendorChecklist checklist={mockChecklist} onToggleComplete={handleToggle} />);

    const toggleButton = screen.getByRole("button", {
      name: /toggle completion for confirm tasting menu/i,
    });
    await user.click(toggleButton);

    expect(handleToggle).toHaveBeenCalledWith(mockChecklist.items[0]);
  });

  it("triggers edit, delete, and add handlers", async () => {
    const user = userEvent.setup();
    const handleEdit = vi.fn();
    const handleDelete = vi.fn();
    const handleAdd = vi.fn();

    render(
      <VendorChecklist
        checklist={mockChecklist}
        onEditItem={handleEdit}
        onDeleteItem={handleDelete}
        onAddItem={handleAdd}
      />,
    );

    const addButton = screen.getByRole("button", { name: /add checklist item/i });
    await user.click(addButton);
    expect(handleAdd).toHaveBeenCalledTimes(1);

    const editButton = screen.getByRole("button", {
      name: /edit confirm tasting menu/i,
    });
    await user.click(editButton);
    expect(handleEdit).toHaveBeenCalledWith(mockChecklist.items[0]);

    const deleteButton = screen.getByRole("button", {
      name: /delete confirm tasting menu/i,
    });
    await user.click(deleteButton);
    expect(handleDelete).toHaveBeenCalledWith("item-1");
  });

  it("renders empty state when there are no items", () => {
    render(
      <VendorChecklist
        checklist={{
          event_id: "evt-empty",
          total_items: 0,
          completed_items: 0,
          items: [],
        }}
      />,
    );

    expect(screen.getByText(/no checklist items yet/i)).toBeInTheDocument();
  });

  it("passes jest-axe accessibility checks with no violations", async () => {
    const { container } = render(
      <VendorChecklist
        checklist={mockChecklist}
        onToggleComplete={vi.fn()}
        onEditItem={vi.fn()}
        onDeleteItem={vi.fn()}
        onAddItem={vi.fn()}
      />,
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
