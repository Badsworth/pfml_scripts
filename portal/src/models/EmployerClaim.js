/* eslint sort-keys: ["error", "asc"] */
import BaseBenefitsApplication from "./BaseBenefitsApplication";
import { merge } from "lodash";

/**
 * This model represents a Claim record that is formed from data directly pulled
 * from the Claims Processing System (CPS). This should not be confused with a record
 * from the API's Claims table, which is represented by the Claim model.
 * TODO (EMPLOYER-1130): Rename this model to clarify this nuance.
 */
class EmployerClaim extends BaseBenefitsApplication {
  get defaults() {
    return merge({
      ...super.defaults,
      employer_dba: null,
      employer_id: null,
      follow_up_date: null,
      is_reviewable: null,
      // array of PreviousLeave objects. See the PreviousLeave model
      previous_leaves: [],
    });
  }
}

export default EmployerClaim;
