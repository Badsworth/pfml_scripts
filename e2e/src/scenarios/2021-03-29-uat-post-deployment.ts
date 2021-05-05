import { parseISO, addDays, addWeeks } from "date-fns";
import { ScenarioSpecification } from "../generation/Scenario";

// Deny claim for financial eligibility
export const UATP_A: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "UATP_A",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    docs: {},
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 4)],
  },
};

// Deny claim for financial eligibility
export const UATP_B: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "UATP_B",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    docs: {},
    reduced_leave_spec: "0,240,240,240,240,240,0",
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 5)],
  },
};

// Deny claim for financial eligibility
export const UATP_C: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "UATP_C",
    reason: "Pregnancy/Maternity",
    work_pattern_spec: "standard",
    docs: {},
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 5)],
  },
};

// Deny claim for financial eligibility
export const UATP_D: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "UATP_D",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    work_pattern_spec: "standard",
    docs: {},
    bondingDate: "past",
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 5)],
  },
};

// Deny claim for financial eligibility
export const UATP_E: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "UATP_E",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    work_pattern_spec: "standard",
    docs: {},
    bondingDate: addWeeks(new Date(), 1),
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 5)],
  },
};

// Deny claim for financial eligibility
export const UATP_F: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "UATP_F",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    work_pattern_spec: "standard",
    has_intermittent_leave_periods: true,
    docs: {},
    bondingDate: "past",
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 5)],
  },
};

// Deny claim for financial eligibility
export const UATP_G: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "UATP_G",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    docs: {},
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 4)],
  },
};

// Deny claim for financial eligibility
export const UATP_H: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "UATP_H",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    docs: {},
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 4)],
  },
};

// Deny claim for financial eligibility
export const UATP_I: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "UATP_I",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    work_pattern_spec: "standard",
    docs: {},
    bondingDate: "past",
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 5)],
  },
};

// Deny claim for financial eligibility
export const UATP_J: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "UATP_J",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    docs: {},
    bondingDate: "past",
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 5)],
  },
};

// Deny claim for financial eligibility
export const UATP_K: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "UATP_K",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    work_pattern_spec: "standard",
    docs: {},
    bondingDate: "past",
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 5)],
  },
};

export const UATP_L: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "UATP_L",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    docs: {},
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 5)],
  },
};

export const UATP_M: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "UATP_M",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    work_pattern_spec: "standard",
    docs: {},
    bondingDate: "past",
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 5)],
  },
};

export const UATP_N: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "UATP_N",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    docs: {},
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 5)],
  },
};

export const UATP_O: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "UATP_O",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    has_intermittent_leave_periods: true,
    docs: {},
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 5)],
  },
};

export const UATP_P: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "UATP_P",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    work_pattern_spec: "standard",
    docs: {},
    bondingDate: "past",
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 5)],
  },
};
