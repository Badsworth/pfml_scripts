import {
  BondingFosterClaim,
  CaringLeaveClaim,
  MilitaryCaregiverClaim,
  MilitaryExigencyClaim,
  ScenarioSpecification,
} from "../generation/Scenario";
import { addWeeks, subWeeks, startOfWeek, addDays, subDays } from "date-fns";
const mostRecentSunday = startOfWeek(new Date());
const midweek = addDays(mostRecentSunday, 3);

/**
 * Cypress Testing Scenarios.
 *
 * 99% of our Cypress scenarios are short claims (1 day). If you add a new scenario here, please ensure it is a
 * short claim, or you explain why it is not.
 */
export const BHAP1: ScenarioSpecification<BondingFosterClaim> = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "BHAP1",
    shortClaim: true,
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    work_pattern_spec: "0,720,0,720,0,720,0",
    docs: {
      MASSID: {},
      FOSTERPLACEMENT: {},
    },
  },
};

export const BHAP1ER: ScenarioSpecification = {
  ...BHAP1,
  claim: {
    ...BHAP1.claim,
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
  },
};

export const REDUCED_ER: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "REDUCEDER",
    shortClaim: true,
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    docs: {
      FOSTERPLACEMENT: {},
      MASSID: {},
    },
    employerResponse: {
      hours_worked_per_week: 20,
      employer_decision: "Approve",
      fraud: "No",
    },
    reduced_leave_spec: "0,240,240,240,240,240,0",
  },
};

export const REDUCED_ER_MIDWEEK: ScenarioSpecification = {
  ...REDUCED_ER,
  claim: {
    ...REDUCED_ER.claim,
    label: "REDUCED_ER_MIDWEEK",
    shortClaim: false,
    leave_dates: [addWeeks(midweek, 1), addWeeks(midweek, 4)],
  },
};
export const MIL_RED: ScenarioSpecification<MilitaryCaregiverClaim> = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "MIL_RED",
    shortClaim: true,
    reason: "Military Caregiver",
    docs: {
      MASSID: {},
      COVERED_SERVICE_MEMBER_ID: {},
      CARING: {},
    },
    reduced_leave_spec: "0,240,240,240,240,240,0",
  },
};

export const MIL_EXI: ScenarioSpecification<MilitaryExigencyClaim> = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "Military Exigency claim",
    shortClaim: true,
    reason: "Military Exigency Family",
    docs: {
      MASSID: {},
      ACTIVE_SERVICE_PROOF: {},
      MILITARY_EXIGENCY_FORM: {},
    },
  },
};

export const MED_INTER_INEL: ScenarioSpecification = {
  employee: { mass_id: true, wages: "ineligible" },
  claim: {
    label: "MED_INTER_INEL",
    shortClaim: true,
    reason: "Serious Health Condition - Employee",
    docs: {
      HCP: {},
      MASSID: {},
    },
    intermittent_leave_spec: true,
  },
};

export const MCAP_NODOC: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "MCAP_NODOC",
    shortClaim: true,
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "0,315,315,315,315,315,0",
    docs: {
      // Missing HCP.
      MASSID: {},
    },
  },
};

// Only used in *ignored* spec MHAP4.ts
export const MHAP4: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "MHAP4",
    shortClaim: true,
    reason: "Pregnancy/Maternity",
    docs: {
      MASSID: {},
      PREGNANCY_MATERNITY_FORM: {},
    },
  },
};

export const MRAP30: ScenarioSpecification = {
  employee: {
    wages: 30000,
    mass_id: true,
  },
  claim: {
    label: "MRAP30",
    reason: "Serious Health Condition - Employee",
    docs: {
      MASSID: {},
      HCP: {},
    },
    work_pattern_spec: "standard",
    reduced_leave_spec: "0,240,240,240,240,240,0",
    // This scenario requires a 2 week leave time for payment calculation purposes.
    leave_dates: [addWeeks(mostRecentSunday, 1), addWeeks(mostRecentSunday, 3)],
    metadata: { expected_weekly_payment: "230.77" },
  },
};

export const BCAP90: ScenarioSpecification = {
  employee: {
    wages: 90000,
    mass_id: true,
  },
  claim: {
    label: "BCAP90",
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    work_pattern_spec: "0,720,0,720,0,720,0",
    docs: {
      MASSID: {},
      FOSTERPLACEMENT: {},
    },
    // This scenario requires a 2 week leave time for payment calculation purposes.
    leave_dates: [subWeeks(mostRecentSunday, 1), addWeeks(mostRecentSunday, 1)],
    metadata: { expected_weekly_payment: "1084.31" },
  },
};

export const BIAP60: ScenarioSpecification = {
  employee: {
    wages: 60000,
    mass_id: true,
  },
  claim: {
    label: "BIAP60",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    bondingDate: "past",
    work_pattern_spec: "0,240,240,240,240,240,0",
    docs: {
      MASSID: {},
      BIRTHCERTIFICATE: {},
    },
    intermittent_leave_spec: {
      duration: 5,
      duration_basis: "Days",
    },
    is_withholding_tax: false,
    // This scenario requires a 4 week leave time for payment calculation purposes.
    leave_dates: [subWeeks(mostRecentSunday, 4), mostRecentSunday],
    metadata: {
      expected_weekly_payment: "831.06",
      spanHoursStart: "4",
      spanHoursEnd: "4",
    },
  },
};

export const BIAP60ER: ScenarioSpecification = {
  ...BIAP60,
  claim: {
    ...BIAP60.claim,
    label: "BIAP60ER",
    employerResponse: {
      hours_worked_per_week: 20,
      employer_decision: "Approve",
      fraud: "No",
    },
  },
};

export const CCAP90: ScenarioSpecification = {
  employee: {
    wages: 90000,
    mass_id: true,
  },
  claim: {
    label: "CCAP90",
    reason: "Care for a Family Member",
    work_pattern_spec: "0,720,0,720,0,720,0",
    docs: { MASSID: {}, CARING: {} },
    leave_dates: [subWeeks(mostRecentSunday, 1), addWeeks(mostRecentSunday, 1)],
    metadata: { expected_weekly_payment: "1084.31" },
  },
};

export const CCAP90ER: ScenarioSpecification = {
  ...CCAP90,
  claim: {
    ...CCAP90.claim,
    employerResponse: {
      employer_decision: "Approve",
      hours_worked_per_week: 40,
    },
  },
};

export const CDENY2: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "CDENY2",
    shortClaim: true,
    has_continuous_leave_periods: true,
    reason: "Care for a Family Member",
    docs: {
      MASSID: {},
      CARING: {},
    },
  },
};

export const CDENY2ER: ScenarioSpecification = {
  ...CDENY2,
  claim: {
    ...CDENY2.claim,
    employerResponse: {
      employer_decision: "Approve",
      hours_worked_per_week: 40,
    },
  },
};

export const ORGUNIT: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "ORGUNIT",
    shortClaim: true,
    has_continuous_leave_periods: true,
    reason: "Care for a Family Member",
    docs: {
      MASSID: {},
      CARING: {},
    },
    metadata: {
      orgunits: "Division of Administrative Law Appeals",
      worksite: "TEAMX_",
    },
  },
};

// only used in ignored `reductions.ts` spec
export const MED_OLB: ScenarioSpecification = {
  employee: { mass_id: true, wages: 90000 },
  claim: {
    label: "MED with Other Leaves & Benefits",
    leave_dates: [subWeeks(mostRecentSunday, 3), addWeeks(mostRecentSunday, 3)],
    reason: "Serious Health Condition - Employee",
    docs: {
      MASSID: {},
      HCP: {},
    },
    reduced_leave_spec: "0,240,240,240,240,240,0",
    employerResponse: {
      hours_worked_per_week: 20,
      employer_decision: "Approve",
      fraud: "No",
    },
    other_incomes: [
      {
        income_type: "Earnings from another employment/self-employment",
        income_amount_dollars: 200,
        income_amount_frequency: "Per Week",
      },
    ],
    employer_benefits: [
      {
        benefit_amount_dollars: 1000,
        benefit_amount_frequency: "In Total",
        benefit_type: "Short-term disability insurance",
        is_full_salary_continuous: false,
      },
    ],
    previous_leaves_other_reason: [
      {
        type: "other_reason",
        leave_reason: "Bonding with my child after birth or placement",
        is_for_current_employer: true,
        leave_minutes: 2400,
        worked_per_week_minutes: 1200,
      },
    ],
  },
};

export const CONCURRENT: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "CONCURRENT",
    shortClaim: true,
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "0,315,315,315,315,315,0",
    docs: {
      MASSID: {},
      //HCP: {}
    },
    concurrent_leave: { is_for_current_employer: true },
  },
};

export const PREBIRTH: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "PREBIRTH",
    reason: "Pregnancy/Maternity",
    pregnant_or_recent_birth: undefined,
    shortClaim: true,
    docs: {
      MASSID: {},
      PREGNANCY_MATERNITY_FORM: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
  },
};

export const CHAP_RFI: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "CHAP_RFI",
    reason: "Care for a Family Member",
    shortClaim: true,
    docs: {
      MASSID: {},
      CARING: {},
    },
  },
};

export const CONTINUOUS_MEDICAL_OLB: ScenarioSpecification = {
  employee: { mass_id: true, wages: 90000 },
  claim: {
    label: "CONTINUOUS MEDICAL LEAVE WITH OTHER LEAVES & BENEFITS",
    reason: "Serious Health Condition - Employee",
    docs: {
      MASSID: {},
      HCP: {},
    },
    work_pattern_spec: "standard",
    // Create a leave in progress, so we can check adjustments for both made and future payments.
    leave_dates: [subWeeks(mostRecentSunday, 3), addWeeks(mostRecentSunday, 3)],
    // Leave start & end dates here and in employer benefits empty so they match the leave dates automatically
    other_incomes: [
      {
        income_type: "Earnings from another employment/self-employment",
        income_amount_dollars: 200,
        income_amount_frequency: "Per Week",
      },
    ],
    employer_benefits: [
      {
        benefit_amount_dollars: 100,
        benefit_amount_frequency: "Per Week",
        benefit_type: "Short-term disability insurance",
        is_full_salary_continuous: false,
      },
    ],
    previous_leaves_other_reason: [
      {
        type: "other_reason",
        leave_reason: "Bonding with my child after birth or placement",
        is_for_current_employer: true,
        leave_minutes: 2400,
        worked_per_week_minutes: 1200,
      },
    ],
    concurrent_leave: { is_for_current_employer: true },
    metadata: { expected_weekly_payment: "1084.31" },
  },
};

export const BHAP1_OLB: ScenarioSpecification = {
  employee: { mass_id: true, wages: 90000 },
  claim: {
    label: "BHAP1_OLB",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    bondingDate: "future",
    docs: {
      MASSID: {},
      BIRTHCERTIFICATE: {},
    },
    // Create a leave in progress, so we can check adjustments for both made and future payments.
    leave_dates: [subWeeks(mostRecentSunday, 2), addWeeks(mostRecentSunday, 2)],
    // Leave start & end dates here and in employer benefits empty so they match the leave dates automatically
    other_incomes: [
      {
        income_type: "SSDI",
        income_amount_dollars: 200,
        income_amount_frequency: "Per Week",
      },
    ],
    employer_benefits: [
      {
        benefit_amount_dollars: 500,
        benefit_amount_frequency: "In Total",
        benefit_type: "Family or medical leave insurance",
        is_full_salary_continuous: true,
      },
    ],
    previous_leaves_other_reason: [
      {
        type: "other_reason",
        leave_reason: "An illness or injury",
        is_for_current_employer: true,
        leave_minutes: 2400,
        worked_per_week_minutes: 1200,
      },
    ],
    is_withholding_tax: true,
    concurrent_leave: { is_for_current_employer: true },
    metadata: { expected_weekly_payment: "1084.31" },
  },
};

// This needs a specific scenario to be used by a CPS test. Please do not change specs on this scenario.
export const MHAP1_OLB_ER: ScenarioSpecification = {
  employee: { wages: 30000, mass_id: true },
  claim: {
    label: "MHAP1_OLB_ER",
    reason: "Serious Health Condition - Employee",
    // Create a leave in progress, so we can check adjustments for both made and future payments.
    leave_dates: [subWeeks(mostRecentSunday, 3), addWeeks(mostRecentSunday, 1)],
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      employer_decision: "Approve",
      hours_worked_per_week: 40,
    },
  },
};

export const CPS_MID_WK: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "CPS_MID_WK",
    reason: "Serious Health Condition - Employee",
    docs: {
      MASSID: {},
      HCP: {},
    },
    work_pattern_spec: "standard",
    has_continuous_leave_periods: true,
    leave_dates: [subWeeks(midweek, 3), addWeeks(midweek, 3)],
    metadata: { expected_weight: "0.20" },
  },
};

// This only being used for CPS Service Pack testing.
const currentDate = new Date();
/* eslint-disable unused-imports/no-unused-vars */
const startDate = addDays(currentDate, 65);
const endDate = addDays(currentDate, 90);
/* eslint-enable unused-imports/no-unused-vars */
export const CPS_SP: ScenarioSpecification = {
  // @todo wages can be adjusted from eligible/ineligible to wage per year
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "CPS_SP",
    // @todo Choose a reason for leave? If Child Bonding need a reason_qualifier.
    // reason: "Serious Health Condition - Employee",
    reason: "Care for a Family Member",
    // reason: "Pregnancy/Maternity",
    // reason: "Child Bonding",
    // @todo Pregnant or birth leave option in Portal.
    // pregnant_or_recent_birth: true,
    // @todo Choose a reason_qualifier "Newborn" | "Adoption" | "Foster Care" for Child Bonding?
    // reason_qualifier: "Foster Care",
    // @todo Documents must be update for each reason. MASSID is used for all.
    docs: {
      MASSID: {},
      // HCP: {},
      // FOSTERPLACEMENT: {},
      CARING: {},
      // PREGNANCY_MATERNITY_FORM: {},
    },
    // @todo Adjust work pattern if needed?
    work_pattern_spec: "standard",
    // work_pattern_spec: "0,240,240,240,240,240,0",
    // @todo Choose which leave period continuous, intermittent, and reduced? (240 mins = 4 hrs)
    has_continuous_leave_periods: true,
    // intermittent_leave_spec: true,
    // reduced_leave_spec: "0,240,240,240,240,240,0",
    // @todo Choose the period of time for the leave here?
    // @todo If care leave use the start, end.
    // leave_dates: [startDate, endDate],
    // @todo If you want certain days from today.
    leave_dates: [subDays(currentDate, 10), addDays(currentDate, 10)],
    // @todo this will start most recent Sunday with weeks.
    // leave_dates: [subWeeks(mostRecentSunday, 2), addWeeks(mostRecentSunday, 3)],
    is_withholding_tax: true,
  },
};

export const CHAP_ER: ScenarioSpecification = {
  ...CHAP_RFI,
  claim: {
    ...CHAP_RFI.claim,
    label: "CHAP_ER",
    employerResponse: {
      employer_decision: "Approve",
      hours_worked_per_week: 40,
    },
  },
};

export const WDCLAIM: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "WDCLAIM",
    shortClaim: true,
    reason: "Serious Health Condition - Employee",
    docs: {
      HCP: {},
      MASSID: {},
    },
  },
};

export const HIST_CASE: ScenarioSpecification<CaringLeaveClaim> = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "HIST_CASE",
    shortClaim: true,
    has_continuous_leave_periods: true,
    reason: "Care for a Family Member",
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    docs: {
      MASSID: {},
      CARING: {},
    },
  },
};

// Leave start date change request
export const MED_LSDCR: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "MED_LSDCR",
    shortClaim: true,
    reason: "Serious Health Condition - Employee",
    leave_dates: [addWeeks(new Date(), 2), addWeeks(new Date(), 6)],
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    docs: {
      HCP: {},
      MASSID: {},
    },
  },
};

export const MED_ERRE: ScenarioSpecification = {
  employee: {
    wages: 30000,
    mass_id: true,
  },
  claim: {
    label: "MED_ERRE",
    shortClaim: true,
    reason: "Serious Health Condition - Employee",
    leave_dates: [subWeeks(mostRecentSunday, 2), addWeeks(mostRecentSunday, 2)],
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
      employer_benefits: [],
    },
    docs: {
      HCP: {},
      MASSID: {},
    },
    metadata: {
      expected_weekly_payment: "461.54",
      employerReAmount: 100,
    },
  },
};

export const CARE_TAXES: ScenarioSpecification<CaringLeaveClaim> = {
  employee: { wages: 30000 },
  claim: {
    reason: "Care for a Family Member",
    label: "CARE_TAXES",
    leave_dates: [
      startOfWeek(addDays(new Date(), 60)), // claims must start in 2022 in order to test SIT/FIT withholdings
      startOfWeek(addDays(new Date(), 74)),
    ],
    is_withholding_tax: true,
    work_pattern_spec: "standard",
    reduced_leave_spec: "0,240,240,240,240,240,0",
    docs: { CARING: {}, MASSID: {} },
  },
};

export const MED_CONT_ER_APPROVE: ScenarioSpecification = {
  employee: { wages: 60000 },
  claim: {
    reason: "Serious Health Condition - Employee",
    label: "MED_CONT_ER_APPROVE",
    leave_dates: [
      startOfWeek(subWeeks(new Date(), 3)),
      startOfWeek(addWeeks(new Date(), 1)),
    ],
    address: {
      city: "Washington",
      line_1: "1600 Pennsylvania Avenue NW",
      state: "DC",
      zip: "20500",
    },
    work_pattern_spec: "standard",
    docs: { MASSID: {}, HCP: {} },
    payment: {
      payment_method: "Check",
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
  },
};
