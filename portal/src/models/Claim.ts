/* eslint sort-keys: ["error", "asc"] */
import { compact, get } from "lodash";

/**
 * A record from the API's Claims table. Could be utilized by Leave Admin and Claimants.
 */
class Claim {
  absence_period_end_date: string | null = null;
  absence_period_start_date: string | null = null;
  claim_status: AbsenceCaseStatusType | null;
  claim_type_description: string | null = null;
  created_at: string;
  employee: ClaimEmployee | null;
  employer: ClaimEmployer;
  fineos_absence_id: string;
  fineos_notification_id: string;
  managed_requirements: ManagedRequirement[];

  constructor(attrs: Claim) {
    Object.assign(this, attrs);
    if (attrs.employee) {
      this.employee = new ClaimEmployee(attrs.employee);
    }
  }
}

/**
 * Employee (claimant) record associated to the Claim
 */
export class ClaimEmployee {
  first_name: string | null = null;
  last_name: string | null = null;
  middle_name: string | null = null;
  other_name: string | null = null;

  constructor(attrs: Partial<ClaimEmployee>) {
    Object.assign(this, attrs);
  }

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
export interface ClaimEmployer {
  employer_dba: string | null;
  employer_fein: string;
  employer_id: string;
}

/**
 * Managed requirements associated to the Claim
 */
export interface ManagedRequirement {
  category: string;
  created_at: string;
  follow_up_date: string | null;
  responded_at: string | null;
  status: "Open" | "Complete" | "Suppressed";
  type: string;
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

export type AbsenceCaseStatusType =
  typeof AbsenceCaseStatus[keyof typeof AbsenceCaseStatus];

export default Claim;
