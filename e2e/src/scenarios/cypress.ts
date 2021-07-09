import { ScenarioSpecification } from "../generation/Scenario";
import { addWeeks, subWeeks, startOfWeek, addDays } from "date-fns";
import { getCaringLeaveStartEndDates } from "../../src/util/claims";

/**
 * Cypress Testing Scenarios.
 *
 * 99% of our Cypress scenarios are short claims (1 day). If you add a new scenario here, please ensure it is a
 * short claim, or you explain why it is not.
 */
export const BHAP1: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "BHAP1",
    shortClaim: true,
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
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

export const MIL_RED: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "MIL_RED",
    shortClaim: true,
    reason: "Care for a Family Member",
    docs: {
      MASSID: {},
      CARING: {},
    },
    reduced_leave_spec: "0,240,240,240,240,240,0",
  },
};

export const BHAP1INEL: ScenarioSpecification = {
  employee: { mass_id: true, wages: "ineligible" },
  claim: {
    label: "BHAP1",
    shortClaim: true,
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    docs: {
      MASSID: {},
      FOSTERPLACEMENT: {},
    },
  },
};

export const BHAP9: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "BHAP9",
    shortClaim: true,
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    docs: {
      HCP: {},
      MASSID: {},
    },
    intermittent_leave_spec: true,
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

export const MHAP1: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "MHAP1",
    shortClaim: true,
    reason: "Serious Health Condition - Employee",
    docs: {
      HCP: {},
      MASSID: {},
    },
  },
};

export const MHAP1ER: ScenarioSpecification = {
  ...MHAP1,
  claim: {
    ...MHAP1.claim,
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
  },
};

export const MHAP4: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "MHAP4",
    shortClaim: true,
    reason: "Pregnancy/Maternity",
    docs: {
      HCP: {},
      MASSID: {},
    },
  },
};

const mostRecentSunday = startOfWeek(new Date());
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
    metadata: { expected_weekly_payment: "850.00" },
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
    reason_qualifier: "Foster Care",
    work_pattern_spec: "0,240,240,240,240,240,0",
    docs: {
      MASSID: {},
      FOSTERPLACEMENT: {},
    },
    intermittent_leave_spec: {
      duration: 5,
      duration_basis: "Days",
    },
    // This scenario requires a 4 week leave time for payment calculation purposes.
    leave_dates: [subWeeks(mostRecentSunday, 3), addWeeks(mostRecentSunday, 1)],
    metadata: {
      expected_weekly_payment: "800.09",
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

const [start, end] = getCaringLeaveStartEndDates();
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
    leave_dates: [start, end],
    metadata: { expected_weekly_payment: "850.00" },
  },
};

export const CDENY2: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "CDENY2",
    shortClaim: true,
    has_continuous_leave_periods: true,
    reason: "Care for a Family Member",
    docs: {},
  },
};

export const MIL_RED_OLB: ScenarioSpecification = {
  employee: { mass_id: true, wages: 90000 },
  claim: {
    label: "MIL_RED with Other Leaves & Benefits",
    leave_dates: [subWeeks(mostRecentSunday, 3), addWeeks(mostRecentSunday, 3)],
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    docs: {
      MASSID: {},
      FOSTERPLACEMENT: {},
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
export const MED_PRE: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "MED_PRE",
    reason: "Serious Health Condition - Employee",
    pregnant_or_recent_birth: true,
    shortClaim: true,
    docs: {
      MASSID: {},
      PREGNANCY_MATERNITY_FORM: {},
    },
  },
};

export const CHAP_RFI: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "CHAP_RFI",
    reason: "Care for a Family Member",
    leave_dates: [start, addDays(start, 2)],
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
    metadata: { expected_weekly_payment: "850.00" },
  },
};

export const BHAP1_OLB: ScenarioSpecification = {
  employee: { mass_id: true, wages: 90000 },
  claim: {
    label: "BHAP1_OLB",
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    docs: {
      MASSID: {},
      FOSTERPLACEMENT: {},
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
    concurrent_leave: { is_for_current_employer: true },
    metadata: { expected_weekly_payment: "850.00" },
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
