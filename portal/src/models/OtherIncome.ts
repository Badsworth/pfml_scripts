class OtherIncome {
  income_amount_dollars: number | null = null;
  income_end_date: string | null = null;
  income_start_date: string | null = null;
  other_income_id: string | null = null;
  income_type: typeof OtherIncomeType[keyof typeof OtherIncomeType] | null =
    null;

  income_amount_frequency:
    | typeof OtherIncomeFrequency[keyof typeof OtherIncomeFrequency]
    | null = null;

  constructor(attrs: Partial<OtherIncome> = {}) {
    Object.assign(this, attrs);
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
} as const;

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
} as const;

export default OtherIncome;
