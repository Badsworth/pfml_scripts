import { ClaimEmployee, ClaimEmployer, ManagedRequirement } from "./Claim";
import { groupBy, orderBy } from "lodash";
import { LeaveReasonType } from "./LeaveReason";

class ClaimDetail {
  absence_periods: AbsencePeriod[] = [];
  application_id: string;
  employee: ClaimEmployee | null;
  employer: ClaimEmployer | null;
  fineos_absence_id: string;
  fineos_notification_id: string;
  has_paid_payments: boolean;
  managed_requirements: ManagedRequirement[] = [];
  outstanding_evidence: {
    employee_evidence: OutstandingEvidence[] | null;
    employer_evidence: OutstandingEvidence[] | null;
  } | null = null;

  payments: PaymentDetail[] = [];

  constructor(attrs?: Partial<ClaimDetail>) {
    if (!attrs) {
      return;
    }

    Object.assign(this, attrs);

    if (attrs.employee) {
      this.employee = new ClaimEmployee(attrs.employee);
    }

    this.absence_periods = this.absence_periods.map(
      (absence_period) => new AbsencePeriod(absence_period)
    );
  }

  /**
   * Get absence_periods grouped by their leave reason
   * @returns {Object} an object that keys arrays of absence periods by their reason e.g { "Child Bonding": [AbsencePeriod] }
   */
  get absencePeriodsByReason() {
    return groupBy(this.absence_periods, "reason");
  }

  /**
   * Determine if claim is a continuous leave claim
   */
  get isContinuous(): boolean {
    return this.absence_periods.some(
      (absence_period) => absence_period.period_type === "Continuous"
    );
  }

  /**
   * Determine if claim is an intermittent leave claim
   */
  get isIntermittent(): boolean {
    return this.absence_periods.some(
      (absence_period) => absence_period.period_type === "Intermittent"
    );
  }

  /**
   * Determine if claim is a reduced schedule leave claim
   */
  get isReducedSchedule(): boolean {
    return this.absence_periods.some(
      (absence_period) => absence_period.period_type === "Reduced Schedule"
    );
  }

  /**
   * Get managed requirements for claim by desc date
   */
  get managedRequirementByFollowUpDate(): ManagedRequirement[] {
    return orderBy(
      this.managed_requirements,
      [(managedRequirement) => managedRequirement.follow_up_date],
      ["desc"]
    );
  }

  get hasApprovedStatus() {
    return this.absence_periods.some(
      (absence_period) =>
        absence_period.request_decision ===
        <AbsencePeriodRequestDecision>"Approved"
    );
  }
}

export type AbsencePeriodRequestDecision =
  | "Cancelled"
  | "Pending"
  | "Approved"
  | "Denied"
  | "Withdrawn";

export class AbsencePeriod {
  absence_period_end_date: string;
  absence_period_start_date: string;
  evidence_status: string | null = null;
  fineos_leave_request_id: string | null = null;
  period_type: "Continuous" | "Intermittent" | "Reduced Schedule";
  reason: LeaveReasonType;
  reason_qualifier_one = "";
  reason_qualifier_two = "";
  request_decision: AbsencePeriodRequestDecision;

  constructor(attrs: Partial<AbsencePeriod> = {}) {
    Object.assign(this, attrs);
  }
}

interface OutstandingEvidence {
  document_name: string;
  is_document_received: boolean;
}

/**
 * Payment response associated with the Claim from API
 */
export interface Payments {
  absence_case_id: string;
  payments: PaymentDetail[];
}

/**
 * Payment details associated with the Claim
 */
export interface PaymentDetail {
  payment_id: string;
  period_start_date: string;
  period_end_date: string;
  amount: number | null;
  sent_to_bank_date: string | null;
  payment_method: string;
  expected_send_date_start: string | null;
  expected_send_date_end: string | null;
  status: string;
}

export default ClaimDetail;
