/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Employer Claim model
 */
import BaseBenefitsApplication from "./BaseBenefitsApplication";
import { merge } from "lodash";

class EmployerClaim extends BaseBenefitsApplication {
  get defaults() {
    return merge({
      ...super.defaults,
      employer_dba: null,
      employer_id: null,
      follow_up_date: null,
      is_reviewable: null,
    });
  }
}

export default EmployerClaim;
