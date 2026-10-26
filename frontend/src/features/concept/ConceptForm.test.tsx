import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { axe } from "jest-axe";
import { ConceptForm } from "./ConceptForm";

describe("ConceptForm", () => {
  it("renders form elements, inspiration chips, and submit button", () => {
    render(<ConceptForm onSubmit={vi.fn()} isLoading={false} />);

    expect(screen.getByText("✨ Design Creative Concept")).toBeInTheDocument();
    expect(screen.getByLabelText(/vibe brief & aesthetic vision/i)).toBeInTheDocument();
    expect(screen.getByText(/quick inspiration/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /generate concept board/i }),
    ).toBeInTheDocument();
  });

  it("populates the brief when an inspiration chip is clicked", async () => {
    const user = userEvent.setup();
    render(<ConceptForm onSubmit={vi.fn()} isLoading={false} />);

    const chip = screen.getByRole("button", {
      name: /\+ rustic-chic bohemian sunset/i,
    });
    await user.click(chip);

    const textarea = screen.getByLabelText(
      /vibe brief & aesthetic vision/i,
    ) as HTMLTextAreaElement;
    expect(textarea.value).toContain(
      "Rustic-Chic Bohemian Sunset with Pampas Grass & Firepits",
    );
  });

  it("submits the vibe brief when submit button is clicked", async () => {
    const user = userEvent.setup();
    const handleSubmit = vi.fn();

    render(<ConceptForm onSubmit={handleSubmit} isLoading={false} />);

    const textarea = screen.getByLabelText(/vibe brief & aesthetic vision/i);
    await user.type(textarea, "Elegant rooftop garden party with jazz");

    const submitBtn = screen.getByRole("button", {
      name: /generate concept board/i,
    });
    await user.click(submitBtn);

    expect(handleSubmit).toHaveBeenCalledWith("Elegant rooftop garden party with jazz");
  });

  it("disables submit button and shows loading spinner when isLoading is true", () => {
    render(<ConceptForm onSubmit={vi.fn()} isLoading={true} defaultBrief="Test brief" />);

    const submitBtn = screen.getByRole("button", {
      name: /crafting concept\.\.\./i,
    });
    expect(submitBtn).toBeDisabled();
  });

  it("passes jest-axe accessibility checks with no violations", async () => {
    const { container } = render(<ConceptForm onSubmit={vi.fn()} isLoading={false} />);

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
