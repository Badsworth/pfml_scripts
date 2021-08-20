import ClaimDetail, {
  AbsencePeriod,
  OutstandingEvidence,
} from "../../src/models/ClaimDetail";
import { ClaimEmployee, ClaimEmployer } from "../../src/models/Claim";

describe("ClaimDetail", () => {
  it("creates an employee and an employer", () => {
    const claimDetail = new ClaimDetail({
      employee: { email_address: "alsofake@fake.com", first_name: "Baxter" },
      employer: { employer_fein: "00-3456789" },
    });
    expect(claimDetail.employee).toBeInstanceOf(ClaimEmployee);
    expect(claimDetail.employee.email_address).toBe("alsofake@fake.com");
    expect(claimDetail.employee.first_name).toBe("Baxter");
    expect(claimDetail.employer).toBeInstanceOf(ClaimEmployer);
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
      claimDetail.outstanding_evidence.employee_evidence[0]
    ).toBeInstanceOf(OutstandingEvidence);
    expect(
      claimDetail.outstanding_evidence.employee_evidence[0].document_name
    ).toBe("First Fake Document Name");
    expect(
      claimDetail.outstanding_evidence.employee_evidence[0].is_document_received
    ).toBe(true);
    expect(
      claimDetail.outstanding_evidence.employee_evidence[1]
    ).toBeInstanceOf(OutstandingEvidence);
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
      claimDetail.outstanding_evidence.employer_evidence[0]
    ).toBeInstanceOf(OutstandingEvidence);
    expect(
      claimDetail.outstanding_evidence.employer_evidence[0].document_name
    ).toBe("Third Fake Document Name");
    expect(
      claimDetail.outstanding_evidence.employer_evidence[0].is_document_received
    ).toBe(true);
    expect(
      claimDetail.outstanding_evidence.employer_evidence[1]
    ).toBeInstanceOf(OutstandingEvidence);
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

  it("groups absence periods by leave_details", () => {
    const claimDetail = new ClaimDetail({
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
    expect(Object.keys(claimDetail.absencePeriodsByReason).length).toBe(2);
    expect(
      claimDetail.absencePeriodsByReason["Serious Health Condition - Employee"]
    ).toBeInstanceOf(Array);
    expect(
      claimDetail.absencePeriodsByReason[
        "Serious Health Condition - Employee"
      ][0]
    ).toBeInstanceOf(AbsencePeriod);
  });
});
