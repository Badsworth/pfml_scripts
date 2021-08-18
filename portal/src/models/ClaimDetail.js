import { ClaimEmployee, ClaimEmployer } from "./Claim";
import BaseModel from "./BaseModel";

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
}

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
