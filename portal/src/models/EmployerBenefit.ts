class EmployerBenefit {
  benefit_amount_dollars: number | null = null;
  benefit_end_date: string | null = null;
  benefit_start_date: string | null = null;
  // this ID field is currently only used by the /applications API in the Claimant portal
  employer_benefit_id: string | null = null;
  is_full_salary_continuous: boolean | null = null;
  benefit_amount_frequency:
    | typeof EmployerBenefitFrequency[keyof typeof EmployerBenefitFrequency]
    | null = null;

  benefit_type:
    | typeof EmployerBenefitType[keyof typeof EmployerBenefitType]
    | null = null;

  constructor(attrs: Partial<EmployerBenefit> = {}) {
    Object.assign(this, attrs);
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
} as const;

/**
 * Enums for the Employer Benefit `benefit_amount_frequency` field
 * @enum {string}
 */
export const EmployerBenefitFrequency = {
  // The ordering here defines the ordering of elements on the page so we override the linter rule
  /* eslint-disable sort-keys */
  daily: "Per Day",
  weekly: "Per Week",
  monthly: "Per Month",
  inTotal: "In Total",
  // Unknown may be displayed to Leave Admins, but isn't
  // an option we display to Claimants
  unknown: "Unknown",
} as const;

export default EmployerBenefit;
