import valueWithFallback from "../../src/utils/valueWithFallback";

describe("valueWithFallback", () => {
  it("returns the value if it's defined", () => {
    const result = valueWithFallback("I'm here");

    expect(result).toBe("I'm here");
  });

  it("returns blank string as default fallback if value is undefined", () => {
    const result = valueWithFallback(undefined);

    expect(result).toBe("");
  });

  it("returns blank string as default fallback if value is null", () => {
    const result = valueWithFallback(undefined);

    expect(result).toBe("");
  });
});
