import { Issue } from "../../src/errors";
import getRelevantIssues from "../../src/utils/getRelevantIssues";

describe("getRelevantIssues", () => {
  it("combines errors and all warnings when the pages argument is empty", () => {
    const errors = [{ field: "a", namespace: "applications" }];
    const warnings = [{ field: "b", namespace: "applications" }];

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
    const errors: Issue[] = [];
    const warnings = [
      { rule: "disallow_foo", namespace: "applications" },
      { field: "not_in_data", namespace: "applications" },
      { field: "first_name", namespace: "applications" },
      { field: "leave_details.employer_notified", namespace: "applications" },
      {
        field: "leave_details.continuous_leave_periods[0].start_date",
        namespace: "applications",
      },
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
    const errors: Issue[] = [];
    const warnings = [{ field: "first_name", namespace: "applications" }];
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
    const errors: Issue[] = [];
    const warnings = [
      { field: "first_name", type: "required", namespace: "applications" },
      { rule: "disallow_foo", namespace: "applications" },
      { rule: "disallow_bar", namespace: "applications" },
      { rule: "min_leave_periods", namespace: "applications" },
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
      { rule: "disallow_foo", namespace: "applications" },
      { rule: "disallow_bar", namespace: "applications" },
    ]);
  });

  it("filters out a warning if its field/rule is not in the pages' list of fields or applicableRules", () => {
    const errors: Issue[] = [];
    const warnings = [
      { field: "first_name", type: "required", namespace: "applications" },
      { field: "ssn", type: "required", namespace: "applications" },
      {
        field: "work_pattern.work_pattern_days[0].minutes",
        type: "required",
        namespace: "applications",
      },
      { rule: "disallow_foo", namespace: "applications" },
      { rule: "disallow_bar", namespace: "applications" },
      { rule: "min_leave_periods", namespace: "applications" },
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
      { field: "first_name", type: "required", namespace: "applications" },
      { rule: "disallow_foo", namespace: "applications" },
      { rule: "disallow_bar", namespace: "applications" },
    ]);
  });

  it("filters only fields that are exact matches", () => {
    const errors: Issue[] = [];
    const warnings = [
      { field: "first_name", type: "required", namespace: "applications" },
      {
        field: "work_pattern.work_pattern_days[0].minutes",
        type: "required",
        namespace: "applications",
      },
      {
        field: "work_pattern.work_pattern_days[5].minutes",
        type: "required",
        namespace: "applications",
      },
    ];
    const pages = [
      {
        meta: {
          applicableRules: ["disallow_foo", "disallow_bar"],
          fields: [
            "first_name",
            "work_pattern.work_pattern_days",
            "work_pattern.work_pattern_days[5].minutes",
          ],
        },
      },
    ];

    const issues = getRelevantIssues(errors, warnings, pages);

    expect(issues).toHaveLength(2);
    expect(issues).toEqual([
      { field: "first_name", type: "required", namespace: "applications" },
      {
        field: "work_pattern.work_pattern_days[5].minutes",
        type: "required",
        namespace: "applications",
      },
    ]);
  });

  it("filters out intermittent leave field warnings if a disallow_hybrid_intermittent_leave warning is present", () => {
    const errors: Issue[] = [];
    const warnings = [
      {
        field: "leave_details.intermittent_leave_periods[0].start_date",
        type: "required",
        namespace: "applications",
      },
      {
        field: "leave_details.intermittent_leave_periods[0].end_date",
        type: "required",
        namespace: "applications",
      },
      { rule: "disallow_hybrid_intermittent_leave", namespace: "applications" },
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
    expect(issues).toEqual([
      { rule: "disallow_hybrid_intermittent_leave", namespace: "applications" },
    ]);
  });

  describe("array wildcard [*]", () => {
    it("includes warnings for a field in any index of an array", () => {
      const errors: Issue[] = [];
      const warnings = [
        { field: "first_name", type: "required", namespace: "applications" },
        {
          field: "work_pattern.work_pattern_days[5].minutes",
          type: "required",
          namespace: "applications",
        },
        {
          field: "work_pattern.work_pattern_days[12].minutes",
          type: "required",
          namespace: "applications",
        },
        { rule: "disallow_foo", namespace: "applications" },
      ];
      const pages = [
        {
          meta: {
            fields: ["work_pattern.work_pattern_days[*].minutes"],
            applicableRules: ["disallow_foo"],
          },
        },
      ];

      const issues = getRelevantIssues(errors, warnings, pages);

      expect(issues).toHaveLength(3);
      expect(issues).toEqual([
        {
          field: "work_pattern.work_pattern_days[5].minutes",
          type: "required",
          namespace: "applications",
        },
        {
          field: "work_pattern.work_pattern_days[12].minutes",
          type: "required",
          namespace: "applications",
        },
        { rule: "disallow_foo", namespace: "applications" },
      ]);
    });

    it("supports array in dot notation", () => {
      const errors: Issue[] = [];
      const warnings = [
        { field: "first_name", type: "required", namespace: "applications" },
        {
          field: "work_pattern.work_pattern_days.5.minutes",
          type: "required",
          namespace: "applications",
        },
        {
          field: "work_pattern.work_pattern_days.12.minutes",
          type: "required",
          namespace: "applications",
        },
        { rule: "disallow_foo", namespace: "applications" },
      ];
      const pages = [
        {
          meta: {
            fields: ["work_pattern.work_pattern_days.*.minutes"],
            applicableRules: ["disallow_foo"],
          },
        },
      ];

      const issues = getRelevantIssues(errors, warnings, pages);

      expect(issues).toHaveLength(3);
      expect(issues).toEqual([
        {
          field: "work_pattern.work_pattern_days.5.minutes",
          type: "required",
          namespace: "applications",
        },
        {
          field: "work_pattern.work_pattern_days.12.minutes",
          type: "required",
          namespace: "applications",
        },
        { rule: "disallow_foo", namespace: "applications" },
      ]);
    });

    it("filters only fields that are exact matches", () => {
      const errors: Issue[] = [];
      const warnings = [
        { field: "first_name", type: "required", namespace: "applications" },
        {
          field: "work_pattern.work_pattern_days[0].minutes",
          type: "required",
          namespace: "applications",
        },
        {
          field: "work_pattern.work_pattern_days[2]",
          type: "required",
          namespace: "applications",
        },
      ];
      const pages = [
        {
          meta: {
            fields: ["work_pattern.work_pattern_days[*]"],
          },
        },
      ];

      const issues = getRelevantIssues(errors, warnings, pages);

      expect(issues).toHaveLength(1);
      expect(issues).toEqual([
        {
          field: "work_pattern.work_pattern_days[2]",
          type: "required",
          namespace: "applications",
        },
      ]);
    });
  });
});
