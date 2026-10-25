import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "jest-axe";
import { EventForm } from "./EventForm";
import type { Event } from "@/shared/contracts";

const mockEvent: Event = {
  id: "evt-123",
  owner_id: "user-123",
  title: "Annual Tech Gala",
  description: "A celebration of modern innovation.",
  event_type: "conference",
  location: "Convention Hall B",
  start_date: "2026-11-20T18:00:00.000Z",
  end_date: "2026-11-20T23:00:00.000Z",
  estimated_guest_count: 250,
  total_budget: 45000,
  currency: "USD",
  status: "planning",
  created_at: "2026-10-24T12:00:00.000Z",
  updated_at: "2026-10-24T12:00:00.000Z",
};

describe("EventForm Component", () => {
  it("renders all form fields when open", () => {
    render(
      <EventForm
        isOpen={true}
        onClose={vi.fn()}
        onSubmit={vi.fn()}
      />
    );

    expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/type/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/location/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/start date/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/end date/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/guest count/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/total budget/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^create$/i })).toBeInTheDocument();
  });

  it("populates initial data when in edit mode", () => {
    render(
      <EventForm
        isOpen={true}
        initialData={mockEvent}
        onClose={vi.fn()}
        onSubmit={vi.fn()}
      />
    );

    expect(screen.getByLabelText(/title/i)).toHaveValue("Annual Tech Gala");
    expect(screen.getByLabelText(/type/i)).toHaveValue("conference");
    expect(screen.getByLabelText(/location/i)).toHaveValue("Convention Hall B");
    expect(screen.getByRole("button", { name: /^update$/i })).toBeInTheDocument();
  });

  it("validates required fields on submission", async () => {
    const handleSubmit = vi.fn();
    render(
      <EventForm
        isOpen={true}
        onClose={vi.fn()}
        onSubmit={handleSubmit}
      />
    );

    const submitBtn = screen.getByRole("button", { name: /^create$/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/title is required/i)).toBeInTheDocument();
    });
    expect(handleSubmit).not.toHaveBeenCalled();
  });

  it("submits valid form data", async () => {
    const user = userEvent.setup();
    const handleSubmit = vi.fn().mockResolvedValue(undefined);

    render(
      <EventForm
        isOpen={true}
        onClose={vi.fn()}
        onSubmit={handleSubmit}
      />
    );

    await user.type(screen.getByLabelText(/title/i), "Sunset Wedding Celebration");
    await user.type(screen.getByLabelText(/location/i), "Golden Gate Beach");
    await user.type(screen.getByLabelText(/start date/i), "2026-12-01T15:00");
    await user.type(screen.getByLabelText(/end date/i), "2026-12-01T22:00");

    const submitBtn = screen.getByRole("button", { name: /^create$/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(handleSubmit).toHaveBeenCalled();
      const calledWith = handleSubmit.mock.calls[0][0];
      expect(calledWith.title).toBe("Sunset Wedding Celebration");
      expect(calledWith.location).toBe("Golden Gate Beach");
    });
  });

  it("has no accessibility violations (jest-axe)", async () => {
    const { container } = render(
      <EventForm
        isOpen={true}
        onClose={vi.fn()}
        onSubmit={vi.fn()}
      />
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
