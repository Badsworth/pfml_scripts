import ClaimDetail from "../../src/models/ClaimDetail";
import { ClaimEmployee } from "../../src/models/Claim";
import LeaveReason from "../../src/models/LeaveReason";
import createMockClaimDetail from "../../lib/mock-helpers/createMockClaimDetail";

describe("ClaimDetail", () => {
  const claimDetailCollection = new ClaimDetail({
    absence_periods: [
      {
        absence_period_start_date: "2021-01-01",
        absence_period_end_date: "2021-06-30",
        reason: "Child Bonding",
      },
      {
        absence_period_start_date: "2021-07-01",
        absence_period_end_date: "2021-12-31",
        reason: "Serious Health Condition - Employee",
      },
      {
        absence_period_start_date: "2021-10-01",
        absence_period_end_date: "2021-12-31",
        reason: "Serious Health Condition - Employee",
      },
    ],
  });
  it("creates an employee and an employer", () => {
    const claimDetail = new ClaimDetail({
      employee: { email_address: "alsofake@fake.com", first_name: "Baxter" },
      employer: { employer_fein: "00-3456789" },
    });
    expect(claimDetail.employee).toBeInstanceOf(ClaimEmployee);
    expect(claimDetail.employee.email_address).toBe("alsofake@fake.com");
    expect(claimDetail.employee.first_name).toBe("Baxter");
    expect(claimDetail.employer).toEqual({ employer_fein: "00-3456789" });
    expect(claimDetail.employer.employer_fein).toBe("00-3456789");
  });

  it("creates employee and employer evidence", () => {
    const claimDetail = new ClaimDetail({
      outstanding_evidence: {
        employee_evidence: [
          {
            document_name: "First Fake Document Name",
            is_document_received: true,
          },
          {
            document_name: "Second Fake Document Name",
            is_document_received: false,
          },
        ],
        employer_evidence: [
          {
            document_name: "Third Fake Document Name",
            is_document_received: true,
          },
          {
            document_name: "Fourth Fake Document Name",
            is_document_received: false,
          },
        ],
      },
    });

    expect(claimDetail.outstanding_evidence.employee_evidence).toBeInstanceOf(
      Array
    );
    expect(claimDetail.outstanding_evidence.employee_evidence.length).toBe(2);

    expect(
      claimDetail.outstanding_evidence.employee_evidence[0].document_name
    ).toBe("First Fake Document Name");
    expect(
      claimDetail.outstanding_evidence.employee_evidence[0].is_document_received
    ).toBe(true);
    expect(
      claimDetail.outstanding_evidence.employee_evidence[1].document_name
    ).toBe("Second Fake Document Name");
    expect(
      claimDetail.outstanding_evidence.employee_evidence[1].is_document_received
    ).toBe(false);

    expect(claimDetail.outstanding_evidence.employer_evidence).toBeInstanceOf(
      Array
    );
    expect(claimDetail.outstanding_evidence.employer_evidence.length).toBe(2);
    expect(
      claimDetail.outstanding_evidence.employer_evidence[0].document_name
    ).toBe("Third Fake Document Name");
    expect(
      claimDetail.outstanding_evidence.employer_evidence[0].is_document_received
    ).toBe(true);
    expect(
      claimDetail.outstanding_evidence.employer_evidence[1].document_name
    ).toBe("Fourth Fake Document Name");
    expect(
      claimDetail.outstanding_evidence.employer_evidence[1].is_document_received
    ).toBe(false);
  });

  it("creates absence periods and sorts by absence_period_start_date", () => {
    const claimDetail = new ClaimDetail({
      absence_periods: [
        {
          absence_period_start_date: "2021-07-01",
          absence_period_end_date: "2021-12-31",
        },
        {
          absence_period_start_date: "2021-01-01",
          absence_period_end_date: "2021-06-30",
        },
      ],
    });
    expect(claimDetail.absence_periods).toBeInstanceOf(Array);
    expect(claimDetail.absence_periods.length).toBe(2);

    expect(claimDetail.absence_periods[0].absence_period_start_date).toBe(
      "2021-01-01"
    );
    expect(claimDetail.absence_periods[0].absence_period_end_date).toBe(
      "2021-06-30"
    );

    expect(claimDetail.absence_periods[1].absence_period_start_date).toBe(
      "2021-07-01"
    );
    expect(claimDetail.absence_periods[1].absence_period_end_date).toBe(
      "2021-12-31"
    );
  });

  it("returns a list of leave dates for the claim", () => {
    expect(claimDetailCollection.leaveDates.length).toBe(3);
    expect(claimDetailCollection.leaveDates[0]).toMatchObject({
      absence_period_end_date: "2021-06-30",
      absence_period_start_date: "2021-01-01",
    });
  });

  it("returns the waiting period for the claim", () => {
    expect(claimDetailCollection.waitingWeek.startDate).toEqual(
      claimDetailCollection.absence_periods[0].absence_period_start_date
    );
    expect(claimDetailCollection.waitingWeek.endDate).toEqual("2021-01-07");
  });

  it("creates employer managed requirements", () => {
    const requirement = {
      category: "test category",
      created_at: "2021-05-30",
      follow_up_date: "2021-06-30",
      responded_at: "2021-07-30",
      status: "Completed",
      type: "test type",
    };

    const managed_requirements = [requirement, requirement];
    const claimDetail = new ClaimDetail({ managed_requirements });

    claimDetail.managed_requirements.forEach((managed_requirement) => {
      expect(managed_requirement).toEqual(requirement);
    });
  });

  describe("#openManagedRequirement", () => {
    it("returns managed requirement sorted by follow up date", () => {
      const requirement = {
        category: "test category",
        created_at: "2021-05-30",
        follow_up_date: "2021-06-30",
        responded_at: "2021-07-30",
        status: "Completed",
        type: "test type",
      };

      const requirement_2 = {
        ...requirement,
        category: "Requirement 2",
        follow_up_date: "2021-07-28",
        status: "Open",
      };

      const managed_requirements = [requirement, requirement_2];
      const claimDetail = new ClaimDetail({ managed_requirements });

      expect(claimDetail.managedRequirementByFollowUpDate).toEqual([
        requirement_2,
        requirement,
      ]);
    });
  });

  it("hasApprovedStatus returns true if a claim has at least one approved status", () => {
    const claimDetail = new ClaimDetail({
      absence_periods: [
        {
          absence_period_start_date: "2021-01-01",
          absence_period_end_date: "2021-06-30",
          reason: "Child Bonding",
          request_decision: "Approved",
        },
        {
          absence_period_start_date: "2021-07-01",
          absence_period_end_date: "2021-12-31",
          reason: "Serious Health Condition - Employee",
          request_decision: "Pending",
        },
        {
          absence_period_start_date: "2021-10-01",
          absence_period_end_date: "2021-12-31",
          reason: "Serious Health Condition - Employee",
          request_decision: "Pending",
        },
      ],
    });

    expect(claimDetail.hasApprovedStatus).toBeTruthy();
  });

  // Getters return true when associated leave type is used
  it.each([
    ["isContinuous", "Continuous"],
    ["isIntermittent", "Intermittent"],
    ["isReducedSchedule", "Reduced Schedule"],
  ])("%s getter returns true when claim is %s", (leaveGetter, leaveType) => {
    const claimDetail = createMockClaimDetail({ leaveType });
    expect(claimDetail[leaveGetter]).toBe(true);
  });

  // Getters return false when associated leave type is not used
  it.each([
    {
      leaveTypeGetter: "isContinuous",
      leaveTypes: ["Intermittent", "Reduced Schedule"],
      leaveTypeTest: "Continuous",
    },
    {
      leaveTypeGetter: "isIntermittent",
      leaveTypes: ["Continuous", "Reduced Schedule"],
      leaveTypeTest: "Intermittent",
    },
    {
      leaveTypeGetter: "isReducedSchedule",
      leaveTypes: ["Continuous", "Intermittent"],
      leaveTypeTest: "Reduced Schedule",
    },
  ])(
    "$leaveTypeGetter getter returns false when claim is not $leaveTypeTest",
    ({ leaveTypeGetter, leaveTypes }) => {
      leaveTypes.forEach((leaveType) => {
        const claimDetail = createMockClaimDetail({ leaveType });
        expect(claimDetail[leaveTypeGetter]).toBe(false);
      });
    }
  );

  describe("#isNonPregnancyMedicalLeave", () => {
    it("returns true when a period has medical leave reason and no pregnancy qualifiers", () => {
      const claimDetail = new ClaimDetail({
        absence_periods: [
          {
            reason: LeaveReason.medical,
          },
        ],
      });

      expect(claimDetail.isNonPregnancyMedicalLeave).toBe(true);
    });

    it("returns false when a period has medical leave reason and pregnancy qualifiers", () => {
      const claimDetail = new ClaimDetail({
        absence_periods: [
          {
            reason: LeaveReason.medical,
            reason_qualifier_one: "Prenatal Disability",
          },
        ],
      });

      const claimDetail2 = new ClaimDetail({
        absence_periods: [
          {
            reason: LeaveReason.bonding,
          },
          {
            reason: LeaveReason.medical,
            reason_qualifier_one: "Prenatal Care",
          },
        ],
      });

      expect(claimDetail.isNonPregnancyMedicalLeave).toBe(false);
      expect(claimDetail2.isNonPregnancyMedicalLeave).toBe(false);
    });

    it("returns false when a period has no medical leave reason", () => {
      const claimDetail = new ClaimDetail({
        absence_periods: [
          {
            reason: LeaveReason.bonding,
          },
        ],
      });

      expect(claimDetail.isNonPregnancyMedicalLeave).toBe(false);
    });
  });

  describe("#isPregnancyLeave", () => {
    it("returns true when period has pregnancy leave", () => {
      const claimDetail = new ClaimDetail({
        absence_periods: [
          {
            reason: LeaveReason.pregnancy,
          },
        ],
      });

      const claimDetail2 = new ClaimDetail({
        absence_periods: [
          {
            reason: LeaveReason.bonding,
          },
          {
            reason: LeaveReason.pregnancy,
          },
        ],
      });

      expect(claimDetail.isPregnancyLeave).toBe(true);
      expect(claimDetail2.isPregnancyLeave).toBe(true);
    });

    it("returns true when period has medical reason and pregnancy qualifier", () => {
      const claimDetail = new ClaimDetail({
        absence_periods: [
          {
            reason: LeaveReason.medical,
            reason_qualifier_one: "Prenatal Disability",
          },
        ],
      });

      const claimDetail2 = new ClaimDetail({
        absence_periods: [
          {
            reason: LeaveReason.bonding,
          },
          {
            reason: LeaveReason.medical,
            reason_qualifier_one: "Prenatal Care",
          },
        ],
      });

      expect(claimDetail.isPregnancyLeave).toBe(true);
      expect(claimDetail2.isPregnancyLeave).toBe(true);
    });

    it("returns false when a period has no pregnancy leave reason", () => {
      const claimDetail = new ClaimDetail({
        absence_periods: [
          {
            reason: LeaveReason.bonding,
          },
        ],
      });

      expect(claimDetail.isPregnancyLeave).toBe(false);
    });
  });

  describe("#isCaringLeave", () => {
    it("returns true when period has caring leave reason", () => {
      const claimDetail = new ClaimDetail({
        absence_periods: [
          {
            reason: LeaveReason.care,
          },
        ],
      });

      expect(claimDetail.isCaringLeave).toBe(true);
    });

    it("returns false when periiod does not have caring leave reason", () => {
      const claimDetail = new ClaimDetail({
        absence_periods: [
          {
            reason: LeaveReason.bonding,
          },
        ],
      });

      expect(claimDetail.isCaringLeave).toBe(false);
    });
  });
});
