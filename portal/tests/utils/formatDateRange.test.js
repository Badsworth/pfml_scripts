import formatDateRange from "../../src/utils/formatDateRange";

describe("formatDateRange", () => {
  describe("when start and date range are valid", () => {
    it("returns formatted date range", () => {
      const formattedDate = formatDateRange("1990-09-01", "1990-10-31");

      expect(formattedDate).toBe("9/1/1990 to 10/31/1990");
    });
  });

  describe("when start and date range are masked", () => {
    it("returns formatted date range with masked fields still masked", () => {
      const formattedDate = formatDateRange("****-09-01", "****-**-**");

      expect(formattedDate).toBe("9/1/**** to **/**/****");
    });
  });

  describe("when start and end dates are invalid ISO 8601 strings", () => {
    it("returns empty string", () => {
      const formattedDate = formatDateRange("1990--", "1990--31");

      expect(formattedDate).toBe("");
    });
  });

  describe("when only start date is present", () => {
    it("does not include date delimiter", () => {
      const formattedDate = formatDateRange("1990-09-01", null);

      expect(formattedDate).toBe("9/1/1990");
    });
  });

  describe("when customDelimiter is present", () => {
    it("overrides the default delimiter", () => {
      const formattedDate = formatDateRange(
        "1990-09-01",
        "1990-10-31",
        "through"
      );

      expect(formattedDate).toBe("9/1/1990 through 10/31/1990");
    });
  });

  describe("when start and end dates are null", () => {
    it("returns blank dates", () => {
      const formattedDate = formatDateRange(null, null);

      expect(formattedDate).toBe("");
    });
  });
});
