import { ScenarioSpecification } from "../generation/Scenario";
import { parseISO } from "date-fns";

export const PERF_APRIL_A: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "PERF_APRIL_A",
    work_pattern_spec: "standard",
    has_continuous_leave_periods: true,
    reason: "Serious Health Condition - Employee",
    leave_dates: [parseISO("2022-02-06"), parseISO("2022-03-13")],
    is_withholding_tax: true,
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    metadata: {
      postSubmit: "APPROVE",
      amount: 20,
    },
  },
};

export const PERF_APRIL_B: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "PERF_APRIL_B",
    work_pattern_spec: "standard",
    has_continuous_leave_periods: true,
    reason: "Serious Health Condition - Employee",
    leave_dates: [parseISO("2022-03-06"), parseISO("2022-05-17")],
    is_withholding_tax: true,
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    metadata: {
      postSubmit: "APPROVE",
      amount: 20,
    },
  },
};

export const PERF_APRIL_C: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "PERF_APRIL_C",
    work_pattern_spec: "standard",
    has_continuous_leave_periods: true,
    reason: "Serious Health Condition - Employee",
    leave_dates: [parseISO("2022-03-20"), parseISO("2022-05-02")],
    is_withholding_tax: true,
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    metadata: {
      postSubmit: "APPROVE",
      amount: 5,
    },
  },
};

export const PERF_APRIL_D: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "PERF_APRIL_D",
    intermittent_leave_spec: {
      duration: 3,
      duration_basis: "Days",
    },
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    bondingDate: "past",
    leave_dates: [parseISO("2022-03-06"), parseISO("2022-05-15")],
    is_withholding_tax: false,
    docs: {
      MASSID: {},
      BIRTHCERTIFICATE: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    metadata: {
      postSubmit: "APPROVE",
      amount: 10,
    },
  },
};

export const PERF_APRIL_E: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "PERF_APRIL_E",
    reduced_leave_spec: "0, 240, 240, 240, 240, 240, 0",
    reason: "Pregnancy/Maternity",
    leave_dates: [parseISO("2022-02-27"), parseISO("2022-05-15")],
    is_withholding_tax: true,
    docs: {
      MASSID: {},
      PREGNANCY_MATERNITY_FORM: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    metadata: {
      postSubmit: "APPROVE",
      amount: 12,
    },
  },
};

export const PERF_APRIL_F: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "PERF_APRIL_F",
    work_pattern_spec: "standard",
    has_continuous_leave_periods: true,
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    leave_dates: [parseISO("2022-03-20"), parseISO("2022-05-17")],
    is_withholding_tax: true,
    docs: {
      MASSID: {},
      FOSTERPLACEMENT: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    metadata: {
      postSubmit: "APPROVE",
      amount: 5,
    },
  },
};

export const PERF_APRIL_G: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "PERF_APRIL_G",
    work_pattern_spec: "standard",
    has_continuous_leave_periods: true,
    reason: "Pregnancy/Maternity",
    leave_dates: [parseISO("2022-03-27"), parseISO("2022-05-15")],
    is_withholding_tax: true,
    docs: {
      MASSID: {},
      PREGNANCY_MATERNITY_FORM: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    metadata: {
      postSubmit: "APPROVE",
      amount: 5,
    },
  },
};

export const PERF_APRIL_H: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "PERF_APRIL_H",
    work_pattern_spec: "standard",
    has_continuous_leave_periods: true,
    reason: "Serious Health Condition - Employee",
    leave_dates: [parseISO("2022-03-06"), parseISO("2022-04-24")],
    is_withholding_tax: false,
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    metadata: {
      amount: 10,
    },
  },
};
