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
      follow_up_date: null,
    });
  }
}

export default EmployerClaim;
