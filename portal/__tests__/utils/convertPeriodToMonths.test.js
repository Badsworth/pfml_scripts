import convertPeriodToMonths from "../../src/utils/convertPeriodToMonths";

describe("convertPeriodToMonths", () => {
  it("converts quarters to month range", () => {
    expect(convertPeriodToMonths("Q12020")).toEqual("October - December 2019");
    expect(convertPeriodToMonths("Q22020")).toEqual("January - March 2020");
    expect(convertPeriodToMonths("Q32020")).toEqual("April - June 2020");
    expect(convertPeriodToMonths("Q42020")).toEqual("July - September 2020");
  });

  it("returns null if parameter is not properly formatted", () => {
    expect(convertPeriodToMonths("Q52020")).toBeNull();
    expect(convertPeriodToMonths("Quarter12020")).toBeNull();
    expect(convertPeriodToMonths("Q120")).toBeNull();
  });
});
