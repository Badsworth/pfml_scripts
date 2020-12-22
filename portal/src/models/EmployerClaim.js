/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Employer Claim model
 */
import BaseClaim from "./BaseClaim";
import { merge } from "lodash";

class EmployerClaim extends BaseClaim {
  get defaults() {
    return merge({
      ...super.defaults,
      employer_dba: null,
      follow_up_date: null,
      is_reviewable: null,
    });
  }
}

export default EmployerClaim;
