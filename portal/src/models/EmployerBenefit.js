/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Employer sponsored benefit
 */
import BaseModel from "./BaseModel";

class EmployerBenefit extends BaseModel {
  get defaults() {
    return {
      benefit_amount_dollars: null,
      benefit_amount_frequency: null,
      benefit_end_date: null,
      benefit_start_date: null,
      benefit_type: null,
    };
  }
}

/**
 * Enums for the EmployerBenefit `benefit_type` field
 * @enum {string}
 * TODO: (CP-567) make sure these enum strings match the API's values
 */
export const EmployerBenefitType = {
  // The ordering here defines the ordering of elements on the page so we override the linter rule
  /* eslint-disable sort-keys */
  paidLeave: "Paid Leave",
  shortTermDisability: "Short Term Disability",
  permanentDisability: "Permanent Disability",
  familyOrMedicalLeave: "Family or Medical Leave",
  /* eslint-enable sort-keys */
};

export default EmployerBenefit;
