import { ClaimEmployee, ClaimEmployer, ManagedRequirement } from "./Claim";

import { AbsencePeriod } from "./AbsencePeriod";
import dayjs from "dayjs";
import { orderBy } from "lodash";

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

    /**
     * Filtering to account for instances where a payment may be sent during the waiting week or prior to the leave start date
     */

    this.payments = this.payments.filter(
      ({ period_start_date, status }) =>
        (this.waitingWeek?.startDate &&
          this.waitingWeek.startDate < period_start_date) ||
        status === "Sent to bank"
    );
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
      (absence_period) => absence_period.request_decision === "Approved"
    );
  }

  get leaveDates(): AbsencePeriodDates[] {
    return this.absence_periods.map(
      ({ absence_period_start_date, absence_period_end_date }) => ({
        absence_period_start_date,
        absence_period_end_date,
      })
    );
  }

  get waitingWeek(): { startDate?: string; endDate?: string } {
    if (this.leaveDates.length) {
      return {
        // API will return absence_periods sorted by start date, waiting week is the first week at the start of the claim
        startDate: this.leaveDates[0].absence_period_start_date,
        endDate: dayjs(this.leaveDates[0].absence_period_start_date)
          .add(6, "days")
          .format("YYYY-MM-DD"),
      };
    }
    return {};
  }
}

interface AbsencePeriodDates {
  absence_period_start_date: string;
  absence_period_end_date: string;
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

export type PaymentStatus =
  | "Cancelled"
  | "Delayed"
  | "Pending"
  | "Sent to bank";

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
  status: PaymentStatus;
}

export default ClaimDetail;
