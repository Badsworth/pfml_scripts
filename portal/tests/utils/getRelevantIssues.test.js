import getRelevantIssues from "../../src/utils/getRelevantIssues";

describe("getRelevantIssues", () => {
  it("combines errors and warnings", () => {
    const errors = [{ field: "a" }];
    const warnings = [{ field: "b" }];

    const issues = getRelevantIssues(errors, warnings);

    expect(issues).toHaveLength(2);
  });

  it("doesn't crash if errors and warnings are undefined", () => {
    const errors = undefined;
    const warnings = undefined;

    const issues = getRelevantIssues(errors, warnings);

    expect(issues).toEqual([]);
  });

  it("filters out warnings not in the filterData argument", () => {
    const errors = [];
    const warnings = [
      { field: "not_in_data" },
      { field: "first_name" },
      { field: "leave_details.employer_notified" },
      { field: "leave_details.continuous_leave_periods[0].start_date" },
    ];
    const filterData = {
      first_name: "",
      leave_details: {
        employer_notified: true,
        continuous_leave_periods: [
          {
            start_date: null,
          },
        ],
      },
    };

    const issues = getRelevantIssues(errors, warnings, filterData);
    const issueFields = issues.map((issue) => issue.field);

    expect(issues).toHaveLength(3);
    expect(issueFields).not.toContain("not_in_data");
    expect(issueFields).toEqual(
      expect.arrayContaining([
        "first_name",
        "leave_details.employer_notified",
        "leave_details.continuous_leave_periods[0].start_date",
      ])
    );
  });
});
