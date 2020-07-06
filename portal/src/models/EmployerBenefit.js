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
  familyOrMedicalLeave: "Family or Medical Leave",
  paidLeave: "Paid Leave",
  permanentDisability: "Permanent Disability",
  shortTermDisability: "Short Term Disability",
};

export default EmployerBenefit;
