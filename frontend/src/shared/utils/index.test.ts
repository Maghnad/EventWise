import { describe, it, expect } from "vitest";
import { cn, formatDate, truncate } from "./index";

describe("shared utils", () => {
  it("cn joins class names and ignores falsy values", () => {
    expect(cn("base-class", false && "hidden", "active")).toBe("base-class active");
  });

  it("truncate cuts long strings with ellipsis", () => {
    expect(truncate("EventWise Assistant", 9)).toBe("EventWis…");
    expect(truncate("Short", 10)).toBe("Short");
  });

  it("formatDate formats valid ISO string", () => {
    const formatted = formatDate("2026-10-24T00:00:00.000Z");
    expect(formatted).toBeDefined();
    expect(typeof formatted).toBe("string");
  });
});
