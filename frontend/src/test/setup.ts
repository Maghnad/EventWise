import "@testing-library/jest-dom";
import { toHaveNoViolations } from "jest-axe";
import { expect } from "vitest";

expect.extend(toHaveNoViolations);

if (typeof window !== "undefined") {
  window.HTMLElement.prototype.scrollIntoView = function () {};
}

