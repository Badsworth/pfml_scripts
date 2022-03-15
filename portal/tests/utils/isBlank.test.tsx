import React from "react";
import isBlank from "../../src/utils/isBlank";

describe("isBlank", () => {
  it("returns true when value is undefined", () => {
    expect(isBlank(undefined)).toBe(true);
  });

  it("returns true when value is null", () => {
    expect(isBlank(null)).toBe(true);
  });

  it("returns true when value is empty string", () => {
    expect(isBlank("")).toBe(true);
  });

  it("returns false when value is non-empty string", () => {
    expect(isBlank("abc")).toBe(false);
  });

  it("returns false when value is 0", () => {
    expect(isBlank(0)).toBe(false);
  });

  it("returns false when value is a React node", () => {
    expect(isBlank(<div />)).toBe(false);
  });
});
