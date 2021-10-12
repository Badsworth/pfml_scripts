/* eslint sort-keys: ["error", "asc"] */
import { compact, get } from "lodash";

import BaseModel from "./BaseModel";

/**
 * A record from the API's Claims table. Could be utilized by Leave Admin and Claimants.
 */
class Claim extends BaseModel {
  constructor(attrs) {
    super(attrs);

    // @ts-expect-error ts-migrate(2339) FIXME: Property 'employee' does not exist on type 'Claim'... Remove this comment to see the full error message
    if (this.employee) {
      // @ts-expect-error ts-migrate(2339) FIXME: Property 'employee' does not exist on type 'Claim'... Remove this comment to see the full error message
      this.employee = new ClaimEmployee(this.employee);
    }

    // @ts-expect-error ts-migrate(2339) FIXME: Property 'employer' does not exist on type 'Claim'... Remove this comment to see the full error message
    if (this.employer) {
      // @ts-expect-error ts-migrate(2339) FIXME: Property 'employer' does not exist on type 'Claim'... Remove this comment to see the full error message
      this.employer = new ClaimEmployer(this.employer);
    }
  }

  // @ts-expect-error ts-migrate(2416) FIXME: Property 'defaults' in type 'Claim' is not assigna... Remove this comment to see the full error message
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
      /**
       * @type {ManagedRequirement}
       */
      managed_requirements: null,
    };
  }
}

/**
 * Employee (claimant) record associated to the Claim
 */
export class ClaimEmployee extends BaseModel {
  // @ts-expect-error ts-migrate(2416) FIXME: Property 'defaults' in type 'ClaimEmployee' is not... Remove this comment to see the full error message
  get defaults() {
    return {
      email_address: null,
      first_name: null,
      last_name: null,
      middle_name: null,
      other_name: null,
      phone_number: null,
      tax_identifier_last4: null,
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
  // @ts-expect-error ts-migrate(2416) FIXME: Property 'defaults' in type 'ClaimEmployer' is not... Remove this comment to see the full error message
  get defaults() {
    return {
      employer_dba: null,
      employer_fein: null,
      employer_id: null,
    };
  }
}

/**
 * Managed requirements associated to the Claim
 */
export class ManagedRequirement extends BaseModel {
  // @ts-expect-error ts-migrate(2416) FIXME: Property 'defaults' in type 'ManagedRequirement' i... Remove this comment to see the full error message
  get defaults() {
    return {
      category: null,
      created_at: null,
      follow_up_date: null,
      responded_at: null,
      status: null,
      type: null,
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
} as const;

export default Claim;
