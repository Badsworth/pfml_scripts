import { ScenarioSpecification } from "../generation/Scenario";
import { addWeeks, subWeeks, startOfWeek } from "date-fns";

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
export const BHAP8: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "BHAP8",
    shortClaim: true,
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    docs: {
      HCP: {},
      MASSID: {},
    },
    work_pattern_spec: "standard",
    reduced_leave_spec: "0,240,240,240,240,240,0",
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
export const BGBM1: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "BGBM1",
    shortClaim: true,
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
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
export const Jill: ScenarioSpecification = {
  employee: {
    wages: 30000,
    mass_id: true,
  },
  claim: {
    label: "Jill",
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    docs: {
      MASSID: {},
      FOSTERPLACEMENT: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    // This scenario requires a 2 week leave time for payment calculation purposes.
    leave_dates: [subWeeks(mostRecentSunday, 1), addWeeks(mostRecentSunday, 1)],
  },
};

export const Dave: ScenarioSpecification = {
  employee: {
    wages: 90000,
    mass_id: true,
  },
  claim: {
    label: "Dave",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "0,720,0,720,0,720,0",
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      hours_worked_per_week: 36,
      employer_decision: "Approve",
      fraud: "No",
    },
    // This scenario requires a 2 week leave time for payment calculation purposes.
    leave_dates: [subWeeks(mostRecentSunday, 1), addWeeks(mostRecentSunday, 1)],
  },
};

export const Sally: ScenarioSpecification = {
  employee: {
    wages: 60000,
    mass_id: true,
  },
  claim: {
    label: "Sally",
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    docs: {
      MASSID: {},
      FOSTERPLACEMENT: {},
    },
    employerResponse: {
      hours_worked_per_week: 20,
      employer_decision: "Approve",
      fraud: "No",
    },
    // has_intermittent_leave_periods: true,
    // This scenario requires a 2 week leave time for payment calculation purposes.
    leave_dates: [subWeeks(mostRecentSunday, 1), addWeeks(mostRecentSunday, 1)],
  },
};
