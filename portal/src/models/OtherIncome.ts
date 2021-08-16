/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Other income source
 */
import BaseModel from "./BaseModel";

class OtherIncome extends BaseModel {
  // @ts-expect-error ts-migrate(2416) FIXME: Property 'defaults' in type 'OtherIncome' is not a... Remove this comment to see the full error message
  get defaults() {
    return {
      income_amount_dollars: null,
      income_amount_frequency: null,
      income_end_date: null,
      income_start_date: null,
      income_type: null,
      other_income_id: null,
    };
  }
}

/**
 * Enums for the OtherIncome `income_type` field
 * @enum {string}
 */
export const OtherIncomeType = {
  /* eslint-disable sort-keys */
  workersCompensation: "Workers Compensation",
  unemployment: "Unemployment Insurance",
  ssdi: "SSDI",
  retirementDisability: "Disability benefits under Gov't retirement plan",
  jonesAct: "Jones Act benefits",
  railroadRetirement: "Railroad Retirement benefits",
  otherEmployer: "Earnings from another employment/self-employment",
  // Unknown may be displayed to Leave Admins, but isn't
  // an option we display to Claimants
  unknown: "Unknown",
  /* eslint-enable sort-keys */
};

/**
 * Enums for the OtherIncome `income_amount_frequency` field
 * @enum {string}
 */
export const OtherIncomeFrequency = {
  // The ordering here defines the ordering of elements on the page so we override the linter rule
  /* eslint-disable sort-keys */
  daily: "Per Day",
  weekly: "Per Week",
  monthly: "Per Month",
  inTotal: "In Total",
};

export default OtherIncome;
