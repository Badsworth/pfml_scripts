import { ClaimEmployee, ManagedRequirement } from "./Claim";
import { groupBy, orderBy } from "lodash";

import BaseModel from "./BaseModel";

class ClaimDetail extends BaseModel {
  constructor(attrs) {
    super(attrs);

    // @ts-expect-error ts-migrate(2339) FIXME: Property 'employee' does not exist on type 'ClaimD... Remove this comment to see the full error message
    if (this.employee) {
      // @ts-expect-error ts-migrate(2339) FIXME: Property 'employee' does not exist on type 'ClaimD... Remove this comment to see the full error message
      this.employee = new ClaimEmployee(this.employee);
    }

    // @ts-expect-error ts-migrate(2339) FIXME: Property 'absence_periods' does not exist on type ... Remove this comment to see the full error message
    if (this.absence_periods) {
      // @ts-expect-error ts-migrate(2339) FIXME: Property 'absence_periods' does not exist on type ... Remove this comment to see the full error message
      this.absence_periods = this.absence_periods.map(
        (absence_period) => new AbsencePeriod(absence_period)
      );
    }

    if (
      // @ts-expect-error ts-migrate(2339) FIXME: Property 'outstanding_evidence' does not exist on ... Remove this comment to see the full error message
      this.outstanding_evidence &&
      // @ts-expect-error ts-migrate(2339) FIXME: Property 'outstanding_evidence' does not exist on ... Remove this comment to see the full error message
      this.outstanding_evidence.employee_evidence
    ) {
      // @ts-expect-error ts-migrate(2339) FIXME: Property 'outstanding_evidence' does not exist on ... Remove this comment to see the full error message
      this.outstanding_evidence.employee_evidence =
        // @ts-expect-error ts-migrate(2339) FIXME: Property 'outstanding_evidence' does not exist on ... Remove this comment to see the full error message
        this.outstanding_evidence.employee_evidence.map(
          (evidence) => new OutstandingEvidence(evidence)
        );
    }

    if (
      // @ts-expect-error ts-migrate(2339) FIXME: Property 'outstanding_evidence' does not exist on ... Remove this comment to see the full error message
      this.outstanding_evidence &&
      // @ts-expect-error ts-migrate(2339) FIXME: Property 'outstanding_evidence' does not exist on ... Remove this comment to see the full error message
      this.outstanding_evidence.employer_evidence
    ) {
      // @ts-expect-error ts-migrate(2339) FIXME: Property 'outstanding_evidence' does not exist on ... Remove this comment to see the full error message
      this.outstanding_evidence.employer_evidence =
        // @ts-expect-error ts-migrate(2339) FIXME: Property 'outstanding_evidence' does not exist on ... Remove this comment to see the full error message
        this.outstanding_evidence.employer_evidence.map(
          (evidence) => new OutstandingEvidence(evidence)
        );
    }
  }

  // @ts-expect-error ts-migrate(2416) FIXME: Property 'defaults' in type 'ClaimDetail' is not a... Remove this comment to see the full error message
  get defaults() {
    return {
      /**
       * @type {AbsencePeriod}
       */
      absence_periods: [],
      application_id: null,
      /**
       * @type {ClaimEmployee}
       */
      employee: null,

      employer: null,
      fineos_absence_id: null,
      fineos_notification_id: null,

      managed_requirements: [],
      outstanding_evidence: {
        /**
         * @type {OutstandingEvidence}
         */
        employee_evidence: [],
        /**
         * @type {OutstandingEvidence}
         */
        employer_evidence: [],
      },
    };
  }

  /**
   * Get absence_periods grouped by their leave reason
   * @returns {Object} an object that keys arrays of absence periods by their reason e.g { "Child Bonding": [AbsencePeriod] }
   */
  get absencePeriodsByReason() {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'absence_periods' does not exist on type ... Remove this comment to see the full error message
    return groupBy(this.absence_periods, "reason");
  }

  /**
   * Get managed requirements for claim by desc date
   */
  get managedRequirementByFollowUpDate(): ManagedRequirement[] {
    return orderBy(
      // @ts-expect-error ts-migrate(2339) FIXME: Property 'managed_requirements' does not exist on type ... Remove this comment to see the full error message
      this.managed_requirements,
      [(managedRequirement) => managedRequirement.follow_up_date],
      ["desc"]
    );
  }
}

/**
 * Model for AbsencePeriod Object
 * @property {string} [absence_period_start_date] - Start date of absence period
 * @property {string} [absence_period_end_date] - End date of absence period
 * @property {string} [evidence_status] - Evidence status for documents requested [N/A, Pending, Waived, Satisfied, Not Satisfied, Not Required]
 * @property {string} [fineos_leave_request_id] - Leave request id from Fineos
 * @property {string} [period_type] - Indicates type of absence period type [Continuous, Intermittent, Reduced Schedule]
 * @property {string} [reason] - Absence Period Reason [Care for a Family Member, Pregnancy/Maternity, Child Bonding, Serious Health Condition - Employee]
 * @property {string} [reason_qualifier_one] - First qualifying reason
 * @property {string} [reason_qualifier_two] - Second qualifying reason
 * @property {string} [request_decision] - Status of leave decision [Pending, Approved, Denied, Withdrawn]
 */

export class AbsencePeriod extends BaseModel {
  // @ts-expect-error ts-migrate(2416) FIXME: Property 'defaults' in type 'AbsencePeriod' is not... Remove this comment to see the full error message
  get defaults() {
    return {
      absence_period_end_date: null,
      absence_period_start_date: null,
      evidence_status: null,
      fineos_leave_request_id: null,
      period_type: null,
      reason: null,
      reason_qualifier_one: null,
      reason_qualifier_two: null,
      request_decision: null,
    };
  }
}

export class OutstandingEvidence extends BaseModel {
  // @ts-expect-error ts-migrate(2416) FIXME: Property 'defaults' in type 'OutstandingEvidence' ... Remove this comment to see the full error message
  get defaults() {
    return {
      document_name: null,
      is_document_received: null,
    };
  }
}

export default ClaimDetail;
