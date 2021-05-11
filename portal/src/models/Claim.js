/* eslint sort-keys: ["error", "asc"] */
import { compact, get } from "lodash";
import BaseModel from "./BaseModel";

/**
 * A record from the API's Claims table. Could be utilized by Leave Admin and Claimants.
 */
class Claim extends BaseModel {
  constructor(attrs) {
    super(attrs);

    if (this.employee) {
      this.employee = new ClaimEmployee(this.employee);
    }

    if (this.employer) {
      this.employer = new ClaimEmployer(this.employer);
    }
  }

  get defaults() {
    return {
      absence_period_end_date: null,
      absence_period_start_date: null,
      /**
       * @type {AbsenceCaseStatus}
       */
      claim_status: null,
      claim_type_description: null,
      created_at: null,
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
    };
  }
}

/**
 * Employee (claimant) record associated to the Claim
 */
export class ClaimEmployee extends BaseModel {
  get defaults() {
    return {
      first_name: null,
      last_name: null,
      middle_name: null,
      other_name: null,
    };
  }

  /**
   * @returns {string} Full name, accounting for any false values
   */
  get fullName() {
    return compact([
      get(this, "first_name"),
      get(this, "middle_name"),
      get(this, "last_name"),
    ]).join(" ");
  }
}

/**
 * Employer record associated to the Claim
 */
export class ClaimEmployer extends BaseModel {
  get defaults() {
    return {
      employer_dba: null,
      employer_fein: null,
    };
  }
}

/**
 * Enums for `claim.claim_status` field
 * This is the subset of potential values returned by the API that we show to the user.
 * We currently ignore other potential values like "Adjudication", "Intake In Progress", "Unknown"
 * @enum {string}
 */
export const AbsenceCaseStatus = {
  approved: "Approved",
  closed: "Closed",
  completed: "Completed",
  declined: "Declined",
};

export default Claim;
