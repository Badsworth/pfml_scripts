import getRelevantIssues from "../../src/utils/getRelevantIssues";

describe("getRelevantIssues", () => {
  it("combines errors and all warnings when the pages argument is empty", () => {
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

  it("filters out a warning if its field is not in the pages' list of fields", () => {
    const errors = [];
    const warnings = [
      { rule: "disallow_foo" },
      { field: "not_in_data" },
      { field: "first_name" },
      { field: "leave_details.employer_notified" },
      { field: "leave_details.continuous_leave_periods[0].start_date" },
    ];
    const pages = [
      {
        meta: {
          fields: ["first_name"],
        },
      },
      {
        meta: {
          fields: [
            "leave_details.employer_notified",
            "leave_details.continuous_leave_periods[0].start_date",
          ],
        },
      },
    ];

    const issues = getRelevantIssues(errors, warnings, pages);
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

  it("removes 'claims.' prefix from a page's fields before filtering warning", () => {
    const errors = [];
    const warnings = [{ field: "first_name" }];
    const pages = [
      {
        meta: {
          fields: ["claim.first_name"],
        },
      },
    ];

    const issues = getRelevantIssues(errors, warnings, pages);
    const issueFields = issues.map((issue) => issue.field);

    expect(issueFields).toEqual(expect.arrayContaining(["first_name"]));
  });

  it("filters out a warning if its rule is not in the pages' list of applicableRules", () => {
    const errors = [];
    const warnings = [
      { field: "first_name", type: "required" },
      { rule: "disallow_foo" },
      { rule: "disallow_bar" },
      { rule: "min_leave_periods" },
    ];
    const pages = [
      {
        meta: {
          applicableRules: ["disallow_foo"],
        },
      },
      {
        meta: {
          applicableRules: ["disallow_bar"],
        },
      },
    ];

    const issues = getRelevantIssues(errors, warnings, pages);

    expect(issues).toHaveLength(2);
    expect(issues).toEqual([
      { rule: "disallow_foo" },
      { rule: "disallow_bar" },
    ]);
  });

  it("filters out a warning if its field/rule is not in the pages' list of fields or applicableRules", () => {
    const errors = [];
    const warnings = [
      { field: "first_name", type: "required" },
      { field: "ssn", type: "required" },
      { rule: "disallow_foo" },
      { rule: "disallow_bar" },
      { rule: "min_leave_periods" },
    ];
    const pages = [
      {
        meta: {
          applicableRules: ["disallow_foo", "disallow_bar"],
          fields: ["first_name"],
        },
      },
    ];

    const issues = getRelevantIssues(errors, warnings, pages);

    expect(issues).toHaveLength(3);
    expect(issues).toEqual([
      { field: "first_name", type: "required" },
      { rule: "disallow_foo" },
      { rule: "disallow_bar" },
    ]);
  });

  it("filters out intermittent leave field warnings if a disallow_hybrid_intermittent_leave warning is present", () => {
    const errors = [];
    const warnings = [
      {
        field: "leave_details.intermittent_leave_periods[0].start_date",
        type: "required",
      },
      {
        field: "leave_details.intermittent_leave_periods[0].end_date",
        type: "required",
      },
      { rule: "disallow_hybrid_intermittent_leave" },
    ];
    const pages = [
      {
        meta: {
          applicableRules: ["disallow_hybrid_intermittent_leave"],
          fields: [
            "claim.leave_details.intermittent_leave_periods[0].start_date",
            "claim.leave_details.intermittent_leave_periods[0].end_date",
          ],
        },
      },
    ];

    const issues = getRelevantIssues(errors, warnings, pages);

    expect(issues).toHaveLength(1);
    expect(issues).toEqual([{ rule: "disallow_hybrid_intermittent_leave" }]);
  });
});
