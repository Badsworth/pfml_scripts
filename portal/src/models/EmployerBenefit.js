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
      id: null,
    };
  }
}

/**
 * Enums for the EmployerBenefit `benefit_type` field
 * @enum {string}
 */
export const EmployerBenefitType = {
  /* eslint-disable sort-keys */
  paidLeave: "Accrued paid leave",
  shortTermDisability: "Short-term disability insurance",
  permanentDisability: "Permanent disability insurance",
  familyOrMedicalLeave: "Family or medical leave insurance",
  // Unknown may be displayed to Leave Admins, but isn't
  // an option we display to Claimants
  unknown: "Unknown",
  /* eslint-enable sort-keys */
};

/**
 * Enums for the Employer Benefit `benefit_amount_frequency` field
 * @enum {string}
 */
export const IncomeFrequency = {
  // The ordering here defines the ordering of elements on the page so we override the linter rule
  /* eslint-disable sort-keys */
  daily: "Per Day",
  weekly: "Per Week",
  monthly: "Per Month",
  allAtOnce: "In Total",
};

export default EmployerBenefit;
