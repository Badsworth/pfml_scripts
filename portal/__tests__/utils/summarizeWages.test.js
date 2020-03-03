import { find } from "lodash";
import summarizeWages from "../../src/utils/summarizeWages";

// This is a subset of properties that make up a wage object.
// These are the only properties currently needed to summarize;
const mockWage = (employerId, wages = 5000) => ({
  employer_id: employerId,
  employer_qtr_wages: wages
});

describe("summarizeWages", () => {
  it("totals unique employers", () => {
    // 2 unique employers
    const employer1 = "e72751a0-3ab4-4593-a08b-7f332c359fb4";
    const employer2 = "e4e3a70d-c9bf-4d1e-acf1-e3adefa20a32";

    const wages = [
      mockWage(employer1),
      mockWage(employer1),
      mockWage(employer1),
      mockWage(employer2),
      mockWage(employer2)
    ];

    const { totalEmployers } = summarizeWages(wages);

    expect(totalEmployers).toEqual(2);
  });

  it("sums earnings by employer, rounding to nearest integer and formatting as currency", () => {
    const employer1 = "e72751a0-3ab4-4593-a08b-7f332c359fb4";
    const employer2 = "e4e3a70d-c9bf-4d1e-acf1-e3adefa20a32";

    const wages = [
      mockWage(employer1, 15000.05),
      mockWage(employer1, 20000.01),
      mockWage(employer2, 999.51),
      mockWage(employer2, 3000.02)
    ];

    const { earningsByEmployer } = summarizeWages(wages);
    const employer1Total = find(earningsByEmployer, { employer: employer1 });
    const employer2Total = find(earningsByEmployer, { employer: employer2 });

    expect(employer1Total.earnings).toEqual("$35,000");
    expect(employer2Total.earnings).toEqual("$4,000");
  });
});
