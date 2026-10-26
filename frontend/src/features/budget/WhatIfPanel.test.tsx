import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { axe } from "jest-axe";
import { WhatIfPanel } from "./WhatIfPanel";
import * as budgetApi from "./budgetApi";
import type { WhatIfScenarioResponse } from "@/shared/contracts";

vi.mock("./budgetApi", () => ({
  simulateWhatIfScenario: vi.fn(),
}));

const mockScenarioResponse: WhatIfScenarioResponse = {
  event_id: "evt-123",
  baseline_budget: 30000,
  scenario_budget: 35000,
  budget_variance: 5000,
  baseline_guest_count: 100,
  scenario_guest_count: 125,
  cost_per_guest_baseline: 300,
  cost_per_guest_scenario: 280,
  analysis_summary: "Scaling guest count lowers fixed venue cost per guest.",
  plan: {
    event_type: "wedding",
    guest_count: 125,
    location: "Napa",
    total_budget: 35000,
    items: [
      {
        category: "Catering",
        percentage: 40,
        allocated_amount: 14000,
        notes: "Buffet style with craft cocktails",
      },
      {
        category: "Venue",
        percentage: 25,
        allocated_amount: 8750,
        notes: "Outdoor botanical pavilion",
      },
    ],
  },
};

describe("WhatIfPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders simulator controls, sliders, and reset button", () => {
    render(
      <WhatIfPanel eventId="evt-123" initialBudget={30000} initialGuestCount={100} />,
    );

    expect(
      screen.getByRole("heading", { name: /what-if scenario simulator/i }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/simulated guest count/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/simulated total budget/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /reset simulation to baseline/i }),
    ).toBeInTheDocument();
  });

  it("triggers debounced simulation call when guests or budget changes", async () => {
    vi.mocked(budgetApi.simulateWhatIfScenario).mockResolvedValue(mockScenarioResponse);

    render(
      <WhatIfPanel eventId="evt-123" initialBudget={30000} initialGuestCount={100} />,
    );

    await waitFor(() => {
      expect(budgetApi.simulateWhatIfScenario).toHaveBeenCalledWith(
        "evt-123",
        expect.objectContaining({
          adjusted_budget: 30000,
          adjusted_guest_count: 100,
        }),
      );
    });

    await waitFor(() => {
      expect(screen.getByText("Budget Variance")).toBeInTheDocument();
      expect(screen.getByText("+$5,000")).toBeInTheDocument();
      expect(screen.getByText("125 guests")).toBeInTheDocument();
      expect(screen.getByText("$280.00")).toBeInTheDocument();
      expect(
        screen.getByText(/Scaling guest count lowers fixed venue cost per guest/i),
      ).toBeInTheDocument();
    });
  });

  it("adjusts guest count via increment buttons", async () => {
    const user = userEvent.setup();
    vi.mocked(budgetApi.simulateWhatIfScenario).mockResolvedValue(mockScenarioResponse);

    render(
      <WhatIfPanel eventId="evt-123" initialBudget={30000} initialGuestCount={100} />,
    );

    const plus25Btn = screen.getByRole("button", { name: /\+25 guests/i });
    await user.click(plus25Btn);

    const guestInput = screen.getByLabelText(
      /guest count exact value/i,
    ) as HTMLInputElement;
    expect(guestInput.value).toBe("125");
  });

  it("applies vendor swap preset on click", async () => {
    const user = userEvent.setup();
    vi.mocked(budgetApi.simulateWhatIfScenario).mockResolvedValue(mockScenarioResponse);

    render(
      <WhatIfPanel eventId="evt-123" initialBudget={30000} initialGuestCount={100} />,
    );

    const presetBtn = screen.getByRole("button", {
      name: /Prioritize Gourmet Catering/i,
    });
    await user.click(presetBtn);

    const customInput = screen.getByPlaceholderText(
      /or type custom shift/i,
    ) as HTMLInputElement;
    expect(customInput.value).toBe(
      "Prioritize Gourmet Catering & Craft Cocktails over Venue",
    );
  });

  it("passes jest-axe accessibility checks with no violations", async () => {
    vi.mocked(budgetApi.simulateWhatIfScenario).mockResolvedValue(mockScenarioResponse);

    const { container } = render(
      <WhatIfPanel eventId="evt-123" initialBudget={30000} initialGuestCount={100} />,
    );

    await waitFor(() => {
      expect(budgetApi.simulateWhatIfScenario).toHaveBeenCalled();
    });

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
