import { ScenarioSpecification } from "../generation/Scenario";
import { addWeeks, subWeeks, startOfWeek } from "date-fns";
import { getCaringLeaveStartDate } from "../../src/util/claims";

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
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    docs: {
      HCP: {},
      MASSID: {},
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
    has_intermittent_leave_periods: true,
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
    has_intermittent_leave_periods: true,
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
    leave_dates: [subWeeks(mostRecentSunday, 1), addWeeks(mostRecentSunday, 1)],
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
    has_intermittent_leave_periods: true,
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

export const CCAP90: ScenarioSpecification = {
  employee: {
    wages: 90000,
    mass_id: true,
  },
  claim: {
    label: "CCAP90",
    reason: "Care for a Family Member",
    work_pattern_spec: "0,720,0,720,0,720,0",
    docs: {},
    leave_dates: [
      getCaringLeaveStartDate(),
      addWeeks(getCaringLeaveStartDate(), 2),
    ],
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
