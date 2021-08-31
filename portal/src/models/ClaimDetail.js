import { ClaimEmployee, ClaimEmployer, ManagedRequirement } from "./Claim";

import BaseModel from "./BaseModel";
import { groupBy } from "lodash";

class ClaimDetail extends BaseModel {
  constructor(attrs) {
    super(attrs);

    if (this.employee) {
      this.employee = new ClaimEmployee(this.employee);
    }

    if (this.employer) {
      this.employer = new ClaimEmployer(this.employer);
    }

    if (this.absence_periods) {
      this.absence_periods = this.absence_periods.map(
        (absence_period) => new AbsencePeriod(absence_period)
      );
    }

    if (this.managed_requirements) {
      this.managed_requirements = this.managed_requirements.map(
        (managed_requirement) => new ManagedRequirement(managed_requirement)
      );
    }

    if (
      this.outstanding_evidence &&
      this.outstanding_evidence.employee_evidence
    ) {
      this.outstanding_evidence.employee_evidence =
        this.outstanding_evidence.employee_evidence.map(
          (evidence) => new OutstandingEvidence(evidence)
        );
    }

    if (
      this.outstanding_evidence &&
      this.outstanding_evidence.employer_evidence
    ) {
      this.outstanding_evidence.employer_evidence =
        this.outstanding_evidence.employer_evidence.map(
          (evidence) => new OutstandingEvidence(evidence)
        );
    }
  }

  get defaults() {
    return {
      /**
       * @type {AbsencePeriod}
       */
      absence_periods: [],
      /**
       * @type {ClaimEmployee}
       */
      employee: null,
      /**
       * @type {ClaimEmployer}
       */
      employer: null,
      fineos_absence_id: null,
      fineos_notification_id: null,
      /**
       * @type {ManagedRequirement}
       */
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
    return groupBy(this.absence_periods, "reason");
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
  get defaults() {
    return {
      document_name: null,
      is_document_received: null,
    };
  }
}

export default ClaimDetail;
