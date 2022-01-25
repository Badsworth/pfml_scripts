import formatDate from "../../src/utils/formatDate";

describe("formatDate", () => {
  it("returns full and short functions", () => {
    const format = formatDate("2021-01-13");
    expect(format.full).toBeInstanceOf(Function);
    expect(format.short).toBeInstanceOf(Function);
  });

  describe("full", () => {
    it("returns date formatted as full date", () => {
      const date = formatDate("2021-01-13").full();

      expect(date).toEqual("January 13, 2021");
    });

    it("return empty string when date is invalid", () => {
      // @ts-expect-error Intentionally testing invalid types
      const date1 = formatDate().full();
      const date2 = formatDate("this is not a date").full();
      const date3 = formatDate(null).full();

      expect(date1).toEqual("");
      expect(date2).toEqual("");
      expect(date3).toEqual("");
    });
  });

  describe("short", () => {
    it("returns date formatted as short date", () => {
      const date = formatDate("2021-01-13").short();

      expect(date).toEqual("1/13/2021");
    });

    it("return empty string when date is invalid", () => {
      // @ts-expect-error Intentionally testing invalid types
      const date1 = formatDate().short();
      const date2 = formatDate("this is not a date").short();
      const date3 = formatDate(null).short();

      expect(date1).toEqual("");
      expect(date2).toEqual("");
      expect(date3).toEqual("");
    });

    it("returns short date with masked values when date is masked", () => {
      const date1 = formatDate("****-01-13").short();
      const date2 = formatDate("****-**-**").short();

      expect(date1).toEqual("1/13/****");
      expect(date2).toEqual("**/**/****");
    });

    it("interprets impossible date unexpectedly", () => {
      const date = formatDate("2021-13-14").short();
      expect(date).toEqual("1/14/2022");
    });

    it("requires YYYY-MM-DD input (doesn't detect YYYY-DD-MM)", () => {
      const date = formatDate("2021-16-12").short();
      expect(date).toEqual("4/12/2022");
    });
  });
});
