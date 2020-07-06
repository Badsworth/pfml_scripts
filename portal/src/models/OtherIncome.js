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
 * TODO: (CP-567) make sure these enum strings match the API's values
 */
export const OtherIncomeType = {
  jonesAct: "Jones Act",
  otherEmployer: "Other Employer",
  railroadRetirement: "Railroad Retirement",
  retirementDisability: "Retirement Disability",
  selfEmployment: "Self-Employment",
  ssdi: "SSDI",
  unemployment: "Unemployment",
  workersCompensation: "Workers Comp",
};

export default OtherIncome;
