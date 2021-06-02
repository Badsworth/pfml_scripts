import formatDate from "../../src/utils/formatDate";

describe("formatDate", () => {
  it("returns full and short functions", () => {
    const format = formatDate("2021-01-01");
    expect(format.full).toBeInstanceOf(Function);
    expect(format.short).toBeInstanceOf(Function);
  });

  describe("full", () => {
    it("returns date formatted as full date", () => {
      const date = formatDate("2021-01-01").full();

      expect(date).toEqual("January 1, 2021");
    });

    it("return empty string when date is invalid", () => {
      const date1 = formatDate().full();
      const date2 = formatDate("this is not a date").full();

      expect(date1).toEqual("");
      expect(date2).toEqual("");
    });
  });

  describe("short", () => {
    it("returns date formatted as short date", () => {
      const date = formatDate("2021-01-01").short();

      expect(date).toEqual("1/1/2021");
    });

    it("return empty string when date is invalid", () => {
      const date1 = formatDate().short();
      const date2 = formatDate("this is not a date").short();

      expect(date1).toEqual("");
      expect(date2).toEqual("");
    });

    it("returns short date with masked values when date is masked", () => {
      const date1 = formatDate("****-01-01").short();
      const date2 = formatDate("****-**-**").short();

      expect(date1).toEqual("1/1/****");
      expect(date2).toEqual("**/**/****");
    });
  });
});
