import ClaimDetail from "../../src/models/ClaimDetail";
import { ClaimEmployee } from "../../src/models/Claim";

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

    it("to populate model given ", () => {
      const claimDetail = new ClaimDetail({
        absence_periods: absencePeriod,
        payments: [
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
            amount: 124,
            sent_to_bank_date: null,
            payment_method: "Check",
            expected_send_date_start: "2021-01-24",
            expected_send_date_end: "2021-01-27",
            status: "Pending",
          },
        ],
      });

      expect(claimDetail.payments.length).toBe(2);
      expect(claimDetail.payments[0].period_start_date).toBe("2021-01-08");
      expect(claimDetail.payments[0].period_end_date).toBe("2021-01-15");
      expect(claimDetail.payments[1].status).toBe("Pending");
      expect(claimDetail.payments[1].sent_to_bank_date).toBeNull();
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
});
