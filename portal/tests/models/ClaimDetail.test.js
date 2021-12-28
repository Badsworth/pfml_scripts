import ClaimDetail from "../../src/models/ClaimDetail";
import { ClaimEmployee } from "../../src/models/Claim";
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

  it("creates absence periods", () => {
    const claimDetail = new ClaimDetail({
      absence_periods: [
        {
          absence_period_start_date: "2021-01-01",
          absence_period_end_date: "2021-06-30",
        },
        {
          absence_period_start_date: "2021-07-01",
          absence_period_end_date: "2021-12-31",
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

  describe("creates payments", () => {
    const absencePeriod = [
      {
        absence_period_start_date: "2021-01-01",
        absence_period_end_date: "2021-06-30",
      },
      {
        absence_period_start_date: "2021-07-01",
        absence_period_end_date: "2021-12-31",
      },
    ];

    it("to be initialized as an empty array", () => {
      const claimDetail = new ClaimDetail({
        absence_periods: absencePeriod,
      });

      expect(claimDetail.payments).toBeInstanceOf(Array);
      expect(claimDetail.payments.length).toBe(0);
    });

    it("to populate model given and filter payments with sent_to_bank_date prior to leave start date", () => {
      const samplePayments = [
        {
          payment_id: "12342",
          period_start_date: "2020-12-08",
          period_end_date: "2020-12-15",
          amount: null,
          sent_to_bank_date: null,
          payment_method: "Check",
          expected_send_date_start: null,
          expected_send_date_end: null,
          status: "Cancelled",
        },
        {
          payment_id: "12343",
          period_start_date: "2020-12-01",
          period_end_date: "2020-12-07",
          amount: 124,
          sent_to_bank_date: "2020-12-08",
          payment_method: "Check",
          expected_send_date_start: null,
          expected_send_date_end: null,
          status: "Sent to bank",
        },
        {
          payment_id: "12344",
          period_start_date: "2020-12-16",
          period_end_date: "2020-12-23",
          amount: null,
          sent_to_bank_date: null,
          payment_method: "Check",
          expected_send_date_start: null,
          expected_send_date_end: null,
          status: "Delayed",
        },
        {
          payment_id: "12345",
          period_start_date: "2021-01-08",
          period_end_date: "2021-01-15",
          amount: 124,
          sent_to_bank_date: "2021-01-16",
          payment_method: "Check",
          expected_send_date_start: null,
          expected_send_date_end: null,
          status: "Sent to bank",
        },
        {
          payment_id: "12346",
          period_start_date: "2021-01-16",
          period_end_date: "2021-01-23",
          amount: null,
          sent_to_bank_date: null,
          payment_method: "Check",
          expected_send_date_start: "2021-01-24",
          expected_send_date_end: "2021-01-27",
          status: "Pending",
        },
      ];
      const claimDetail = new ClaimDetail({
        absence_periods: absencePeriod,
        payments: samplePayments,
      });

      expect(claimDetail.payments.length).not.toBe(samplePayments.length);
      const filteredPayments = samplePayments.filter(
        ({ period_start_date, status }) =>
          claimDetail.waitingWeek.startDate < period_start_date ||
          status === "Sent to bank"
      );
      expect(
        filteredPayments.map(({ payment_id }) => payment_id)
      ).toMatchObject(claimDetail.payments.map(({ payment_id }) => payment_id));
    });
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
});
