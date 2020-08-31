/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Other income source
 */
import BaseModel from "./BaseModel";

class OtherIncome extends BaseModel {
  get defaults() {
    return {
      income_amount_dollars: null,
      income_amount_frequency: null,
      income_end_date: null,
      income_start_date: null,
      income_type: null,
    };
  }
}

/**
 * Enums for the OtherIncome `income_type` field
 * @enum {string}
 * TODO (CP-567): make sure these enum strings match the API's values
 */
export const OtherIncomeType = {
  // The ordering of these keys affects the order they're displayed to the user
  /* eslint-disable sort-keys */
  workersCompensation: "Workers Comp",
  unemployment: "Unemployment",
  ssdi: "SSDI",
  retirementDisability: "Retirement Disability",
  jonesAct: "Jones Act",
  railroadRetirement: "Railroad Retirement",
  otherEmployer: "Other Employer",
  selfEmployment: "Self-Employment",
  /* eslint-enable sort-keys */
};

export default OtherIncome;
