/* eslint sort-keys: ["error", "asc"] */
import { compact, get } from "lodash";
import { AbsencePeriod } from "./AbsencePeriod";
import { ManagedRequirement } from "./ManagedRequirement";
import { ValuesOf } from "../../types/common";
import { isReviewable } from "src/utils/isReviewable";

/**
 * A record from the API's Claims table. Could be utilized by Leave Admin and Claimants.
 */
class Claim {
  absence_periods: AbsencePeriod[];
  claim_status: AbsenceCaseStatusType | null;
  created_at: string;
  employee: ClaimEmployee | null;
  employer: ClaimEmployer;
  fineos_absence_id: string;
  managed_requirements: ManagedRequirement[];

  constructor(attrs: Omit<Claim, "isReviewable">) {
    Object.assign(this, attrs);
    if (attrs.employee) {
      this.employee = new ClaimEmployee(attrs.employee);
    }
  }

  /**
   * Note we use a utility method to share logic across EmployerClaim and Claim
   * until such time where we combine these methods (PORTAL-477 pending)
   */
  get isReviewable() {
    return isReviewable(this.absence_periods, this.managed_requirements);
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

export type AbsenceCaseStatusType = ValuesOf<typeof AbsenceCaseStatus>;

export default Claim;
