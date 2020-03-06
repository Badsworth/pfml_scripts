import "../../src/i18n";
import { find } from "lodash";
import summarizeWages from "../../src/utils/summarizeWages";

// This is a subset of properties that make up a wage object.
// These are the only properties currently needed to summarize;
const mockWage = (employerId, wages = 5000, periodId = "Q42020") => ({
  employer_id: employerId,
  period_id: periodId,
  employer_qtr_wages: wages
});

describe("summarizeWages", () => {
  // 2 unique employers
  const employer1 = "e72751a0-3ab4-4593-a08b-7f332c359fb4";
  const employer2 = "e4e3a70d-c9bf-4d1e-acf1-e3adefa20a32";

  it("totals unique employers", () => {
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

  it("sums total earnings by employer, rounding to nearest integer and formatting as currency", () => {
    const wages = [
      mockWage(employer1, 15000.05),
      mockWage(employer1, 20000.01),
      mockWage(employer2, 999.51),
      mockWage(employer2, 3000.02)
    ];

    const { earningsByEmployer } = summarizeWages(wages);
    const employer1Total = find(earningsByEmployer, { employer: employer1 });
    const employer2Total = find(earningsByEmployer, { employer: employer2 });

    expect(employer1Total.totalEarnings).toEqual("$35,000");
    expect(employer2Total.totalEarnings).toEqual("$4,000");
  });

  it("returns wages for an employer with quarter and earnings", () => {
    const wages = [
      mockWage(employer1, 15000.05, "Q12020"),
      mockWage(employer1, 20000.01, "Q22020"),
      mockWage(employer2, 999.51, "Q32020"),
      mockWage(employer2, 3000.02, "Q42020")
    ];

    const { earningsByEmployer } = summarizeWages(wages);
    const employer1Total = find(earningsByEmployer, { employer: employer1 });
    const employer2Total = find(earningsByEmployer, { employer: employer2 });

    expect(employer1Total.wages).toMatchSnapshot([
      {
        employer: employer1,
        earnings: "$15,000",
        quarter: "October - December 2019"
      },
      {
        employer: employer1,
        earnings: "$20,000",
        quarter: "January - March 2020"
      }
    ]);

    expect(employer2Total.wages).toMatchSnapshot([
      {
        employer: employer2,
        earnings: "$1,000",
        quarter: "April - June 2020"
      },
      {
        employer: employer2,
        earnings: "$3,000",
        quarter: "July - September 2020"
      }
    ]);
  });
});
