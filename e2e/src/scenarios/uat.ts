import { subWeeks, addWeeks } from "date-fns";
import { ScenarioSpecification } from "../generation/Scenario";

// Mixed decision variable work pattern
export const UATA: ScenarioSpecification = {
  employee: {
    mass_id: true,
    wages: "eligible",
  },
  claim: {
    label: "UATA",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    work_pattern_spec: "342,342,342,342,342,342,342",
    bondingDate: "past",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 15)],
    docs: {},
  },
};

// Mixed decision fixed work pattern
export const UATB: ScenarioSpecification = {
  employee: {
    mass_id: true,
    wages: "eligible",
  },
  claim: {
    label: "UATB",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    bondingDate: "past",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 15)],
    docs: {},
  },
};

export const UATC: ScenarioSpecification = {
  employee: {
    mass_id: true,
    wages: "eligible",
  },
  claim: {
    label: "UATC",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    bondingDate: "past",
    work_pattern_spec: "0,450,450,450,450,450,0",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 3)],
    docs: {},
  },
};

export const UATD: ScenarioSpecification = {
  employee: {
    mass_id: true,
    wages: "eligible",
  },
  claim: {
    label: "UATD",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    bondingDate: "past",
    work_pattern_spec: "342,342,342,342,342,342,342",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 3)],
    docs: {},
  },
};

export const UATE: ScenarioSpecification = {
  employee: {
    mass_id: true,
    wages: "eligible",
  },
  claim: {
    label: "UATE",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    bondingDate: "past",
    has_intermittent_leave_periods: true,
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 3)],
    docs: {},
  },
};

export const UATF: ScenarioSpecification = {
  employee: {
    mass_id: true,
    wages: "eligible",
  },
  claim: {
    label: "UATF",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    bondingDate: addWeeks(new Date(), 1),
    has_intermittent_leave_periods: true,
    leave_dates: [addWeeks(new Date(), 2), addWeeks(new Date(), 4)],
    docs: {},
  },
};

export const UATG: ScenarioSpecification = {
  employee: {
    mass_id: true,
    wages: "eligible",
  },
  claim: {
    label: "UATG",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    bondingDate: "past",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 3)],
    docs: {},
  },
};

export const UATH: ScenarioSpecification = {
  employee: {
    mass_id: true,
    wages: "eligible",
  },
  claim: {
    label: "UATH",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    bondingDate: addWeeks(new Date(), 1),
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), 2), addWeeks(new Date(), 4)],
    docs: {},
  },
};

export const UATI: ScenarioSpecification = {
  employee: {
    mass_id: true,
    wages: "eligible",
  },
  claim: {
    label: "UATI",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 3)],
    docs: {},
  },
};

export const UATJ: ScenarioSpecification = {
  employee: {
    mass_id: true,
    wages: "eligible",
  },
  claim: {
    label: "UATJ",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 3)],
    docs: {},
  },
};

export const UATK: ScenarioSpecification = {
  employee: {
    mass_id: true,
    wages: "eligible",
  },
  claim: {
    label: "UATK",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: [subWeeks(new Date(), 2), addWeeks(new Date(), 4)],
    docs: {
      MASSID: {},
      HCP: {},
    },
  },
};

export const UATL: ScenarioSpecification = {
  employee: {
    mass_id: true,
    wages: "eligible",
  },
  claim: {
    label: "UATL",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 6)],
    docs: {
      MASSID: {},
      HCP: {},
    },
  },
};

export const UATM: ScenarioSpecification = {
  employee: {
    mass_id: true,
    wages: "eligible",
  },
  claim: {
    label: "UATM",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    bondingDate: addWeeks(new Date(), 1),
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), 2), addWeeks(new Date(), 6)],
    docs: {},
  },
};

export const UATN: ScenarioSpecification = {
  employee: {
    mass_id: true,
    wages: "eligible",
  },
  claim: {
    label: "UATN",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    bondingDate: addWeeks(new Date(), 1),
    reduced_leave_spec: "0,240,240,240,240,240,0",
    work_pattern_spec: "0,480,480,480,480,480,0",
    leave_dates: [addWeeks(new Date(), 2), addWeeks(new Date(), 6)],
    docs: {},
  },
};

export const UATO: ScenarioSpecification = {
  employee: {
    mass_id: true,
    wages: "eligible",
  },
  claim: {
    label: "UATO",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 4)],
    docs: {},
  },
};
export const UATP: ScenarioSpecification = {
  employee: {
    mass_id: true,
    wages: "eligible",
  },
  claim: {
    label: "UATP",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 4)],
    docs: {
      MASSID: {},
      HCP: {},
    },
  },
};

export const UATQ: ScenarioSpecification = {
  employee: {
    mass_id: true,
    wages: "eligible",
  },
  claim: {
    label: "UATQ",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 4)],
    docs: {},
  },
};
