import { ScenarioSpecification } from "../generation/Scenario";
import { parseISO } from "date-fns";

export const TRNOI1: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNOI1",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2021-07-01"), parseISO("2021-10-01")],
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      has_amendments: false,
      fraud: "No",
      employer_decision: "Approve",
      hours_worked_per_week: 40,
    },
    other_incomes: [
      {
        income_type: "Workers Compensation",
        income_start_date: "2021-01-04",
        income_end_date: "2021-07-16",
        income_amount_dollars: 500,
        income_amount_frequency: "Per Week",
      },
    ],
    metadata: {
      postSubmit: "APPROVEDOCS",
    },
  },
};

export const TRNOI2: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNOI2",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2021-07-15"), parseISO("2021-09-15")],
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      has_amendments: false,
      fraud: "No",
      employer_decision: "Approve",
      hours_worked_per_week: 40,
    },
    employer_benefits: [
      {
        benefit_type: "Short-term disability insurance",
        benefit_start_date: "2021-06-07",
        benefit_end_date: "2021-10-10",
        benefit_amount_dollars: 100,
        benefit_amount_frequency: "Per Week",
      },
    ],
    metadata: {
      postSubmit: "APPROVEDOCS",
    },
  },
};

export const TRNOI3: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNOI3",
    reason: "Pregnancy/Maternity",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2021-08-01"), parseISO("2021-10-15")],
    docs: {
      MASSID: {},
      PREGNANCY_MATERNITY_FORM: {},
    },
    employerResponse: {
      has_amendments: false,
      fraud: "No",
      employer_decision: "Approve",
      hours_worked_per_week: 40,
    },
    other_incomes: [
      {
        income_type: "Workers Compensation",
        income_start_date: "2021-05-01",
        income_end_date: "2021-09-01",
        income_amount_dollars: 1000,
        income_amount_frequency: "Per Month",
      },
    ],
    metadata: {
      postSubmit: "APPROVEDOCS",
    },
  },
};

export const TRNOI4: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNOI4",
    reason: "Pregnancy/Maternity",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2021-08-15"), parseISO("2021-11-01")],
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      has_amendments: false,
      fraud: "No",
      employer_decision: "Approve",
      hours_worked_per_week: 40,
    },
    employer_benefits: [
      {
        benefit_type: "Short-term disability insurance",
        benefit_start_date: "2021-08-01",
        benefit_end_date: "2021-12-01",
        benefit_amount_dollars: 100,
        benefit_amount_frequency: "Per Month",
      },
    ],
    metadata: {
      postSubmit: "APPROVEDOCS",
    },
  },
};

export const TRNOL1: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNOL1",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2021-07-15"), parseISO("2021-09-15")],
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      has_amendments: false,
      fraud: "No",
      employer_decision: "Approve",
      hours_worked_per_week: 40,
    },
    previous_leaves_same_reason: [
      {
        type: "same_reason",
        leave_reason: "An illness or injury",
        is_for_current_employer: true,
        leave_start_date: "2021-06-01",
        leave_end_date: "2021-07-15",
        worked_per_week_minutes: 2400,
        leave_minutes: 2400,
      },
    ],
    metadata: {
      postSubmit: "APPROVEDOCS",
    },
  },
};

export const TRNOL2: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNOL2",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2021-07-01"), parseISO("2021-10-01")],
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      has_amendments: false,
      fraud: "No",
      employer_decision: "Approve",
      hours_worked_per_week: 40,
    },
    previous_leaves_same_reason: [
      {
        type: "same_reason",
        leave_reason: "An illness or injury",
        is_for_current_employer: true,
        leave_start_date: "2021-06-01",
        leave_end_date: "2021-07-15",
        worked_per_week_minutes: 2400,
        leave_minutes: 2400,
      },
    ],
    metadata: {
      postSubmit: "APPROVEDOCS",
    },
  },
};

export const TRNOL3: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNOL3",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2021-08-01"), parseISO("2021-10-15")],
    docs: {
      MASSID: {},
      BIRTHCERTIFICATE: {},
    },
    employerResponse: {
      has_amendments: false,
      fraud: "No",
      employer_decision: "Approve",
      hours_worked_per_week: 40,
    },
    previous_leaves_same_reason: [
      {
        type: "same_reason",
        leave_reason: "Bonding with my child after birth or placement",
        is_for_current_employer: true,
        leave_start_date: "2021-06-01",
        leave_end_date: "2021-07-31",
        worked_per_week_minutes: 2400,
        leave_minutes: 2400,
      },
    ],
    metadata: {
      postSubmit: "APPROVEDOCS",
    },
  },
};

export const TRNOL4: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNOL4",
    reason: "Pregnancy/Maternity",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2021-08-15"), parseISO("2021-11-01")],
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      has_amendments: false,
      fraud: "No",
      employer_decision: "Approve",
      hours_worked_per_week: 40,
    },
    concurrent_leave: {
      is_for_current_employer: true,
      leave_start_date: "2021-07-01",
      leave_end_date: "2021-08-30",
    },
    metadata: {
      postSubmit: "APPROVEDOCS",
    },
  },
};

export const TRNER1: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNER1",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2021-07-01"), parseISO("2021-10-01")],
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      has_amendments: true,
      fraud: "No",
      employer_decision: "Approve",
      hours_worked_per_week: 40,
      leave_reason: "Serious Health Condition - Employee",
      previous_leaves: [
        {
          leave_reason: "An illness or injury",
          type: "same_reason",
          leave_start_date: "2021-05-01",
          leave_end_date: "2021-06-30",
        },
      ],
    },
    metadata: {
      postSubmit: "APPROVEDOCS",
    },
  },
};

export const TRNER2: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNER2",
    reason: "Care for a Family Member",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2021-07-15"), parseISO("2021-09-15")],
    docs: {
      MASSID: {},
      // HCP: {},
      CARING: {},
    },
    employerResponse: {
      has_amendments: true,
      fraud: "No",
      employer_decision: "Approve",
      hours_worked_per_week: 40,
      leave_reason: "Care for a Family Member",
      believe_relationship_accurate: "Yes",
      comment: "STD weekly $50",
    },
    metadata: {
      postSubmit: "APPROVEDOCS",
    },
  },
};

export const TRNER3: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNER3",
    reason: "Child Bonding",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2021-08-01"), parseISO("2021-10-15")],
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      has_amendments: true,
      fraud: "No",
      employer_decision: "Approve",
      hours_worked_per_week: 40,
      leave_reason: "Child Bonding",
      concurrent_leave: {
        is_for_current_employer: true,
        leave_start_date: "2021-08-01",
        leave_end_date: "2021-08-30",
      },
    },
    metadata: {
      postSubmit: "APPROVEDOCS",
    },
  },
};
