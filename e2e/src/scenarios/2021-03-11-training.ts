import { ScenarioSpecification } from "../generation/Scenario";

// Deny claim for financial eligibility
export const TRNA: ScenarioSpecification = {
  employee: { mass_id: true, wages: "ineligible" },
  claim: {
    label: "TRNA",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    reduced_leave_spec: "0,240,240,240,240,240,0",
    docs: {
      // MASSID: {},
      // HCP: {},
    },
    metadata: {
      postSubmit: "DENY",
    },
  },
};

// Prep for adjudication
export const TRNB: ScenarioSpecification = {
  employee: { mass_id: true, wages: "ineligible" },
  claim: {
    label: "TRNB",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    reduced_leave_spec: "0,240,240,240,240,240,0",
    docs: {
      MASSID: { invalid: false },
      HCP: { invalid: true },
    },
  },
};

export const TRNC: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNC",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    reduced_leave_spec: "0,240,240,240,240,240,0",
    docs: {
      MASSID: { invalid: true },
      HCP: { invalid: true },
    },
  },
};

export const TRND: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRND",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
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
    },
  },
};

export const TRNE: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNE",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      hours_worked_per_week: 35,
      comment: "$100 disability per week",
    },
  },
};

export const TRNF: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNF",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      hours_worked_per_week: 30,
    },
  },
};

export const TRNG: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNG",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    metadata: {
      postSubmit: "APPROVEDOCS",
    },
  },
};

export const TRNH: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNH",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    docs: {
      MASSID: {},
      HCP: {},
    },
  },
};

export const TRNI: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNI",
    reason: "Serious Health Condition - Employee",
    has_intermittent_leave_periods: true,
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
    },
  },
};

export const TRNJ: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNJ",
    reason: "Serious Health Condition - Employee",
    has_intermittent_leave_periods: true,
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      hours_worked_per_week: 35,
      comment: "$100 disability per week",
    },
  },
};

export const TRNK: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNK",
    reason: "Serious Health Condition - Employee",
    has_intermittent_leave_periods: true,
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      hours_worked_per_week: 30,
    },
  },
};

export const TRNL: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNL",
    reason: "Serious Health Condition - Employee",
    has_intermittent_leave_periods: true,
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    metadata: {
      postSubmit: "APPROVEDOCS",
    },
  },
};

export const TRNM: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNM",
    reason: "Serious Health Condition - Employee",
    has_intermittent_leave_periods: true,
    docs: {
      MASSID: {},
      HCP: {},
    },
  },
};

export const TRNN: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNN",
    reason: "Serious Health Condition - Employee",
    has_intermittent_leave_periods: true,
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      hours_worked_per_week: 35,
      comment: "$100 disability per week",
    },
  },
};

export const TRNO: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNO",
    reason: "Serious Health Condition - Employee",
    has_intermittent_leave_periods: true,
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    metadata: {
      postSubmit: "APPROVEDOCS",
    },
  },
};

// See if it's possible to do intermittent w/ rotating schedule. If it's not possible, we could switch this to continuous leave.
export const TRNP: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNP",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
  },
};

// See if it's possible to do intermittent w/ rotating schedule. If it's not possible, we could switch this to continuous leave.
export const TRNQ: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNQ",
    reason: "Serious Health Condition - Employee",
    has_intermittent_leave_periods: true,
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    metadata: {
      postSubmit: "APPROVEDOCS",
    },
  },
};

export const TRNR: ScenarioSpecification = {
  employee: { mass_id: true, wages: "ineligible" },
  claim: {
    label: "TRNR",
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    docs: {
      // MASSID: {},
      // FOSTERPLACEMENT: {},
    },
  },
};

export const TRNS: ScenarioSpecification = {
  employee: { mass_id: true, wages: "ineligible" },
  claim: {
    label: "TRNS",
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    docs: {
      // MASSID: {},
      // FOSTERPLACEMENT: {},
    },
    metadata: {
      postSubmit: "DENY",
    },
  },
};

// TRNT through TRNAC are bc that should be approved
export const TRNT: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNT",
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
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
    },
  },
};

export const TRNU: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNU",
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    docs: {
      MASSID: {},
      FOSTERPLACEMENT: {},
    },
    employerResponse: {
      hours_worked_per_week: 35,
      comment: "$100 disability per week",
    },
  },
};

export const TRNV: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNV",
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    docs: {
      MASSID: {},
      FOSTERPLACEMENT: {},
    },
    employerResponse: {
      hours_worked_per_week: 30,
    },
  },
};

export const TRNW: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNW",
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    docs: {
      MASSID: {},
      FOSTERPLACEMENT: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    metadata: {
      postSubmit: "APPROVEDOCS",
    },
  },
};

export const TRNX: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNX",
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    docs: {
      MASSID: {},
      FOSTERPLACEMENT: {},
    },
    metadata: {
      postSubmit: "APPROVEDOCS",
    },
  },
};

export const TRNY: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNY",
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    docs: {
      MASSID: {},
      FOSTERPLACEMENT: {},
    },
  },
};

export const TRNZ: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNZ",
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
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
    },
  },
};

export const TRNAA: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNAA",
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    docs: {
      MASSID: {},
      FOSTERPLACEMENT: {},
    },
    employerResponse: {
      hours_worked_per_week: 35,
      comment: "$100 disability per week",
    },
  },
};

export const TRNAB: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNAB",
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    docs: {
      MASSID: {},
      FOSTERPLACEMENT: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    metadata: {
      postSubmit: "APPROVEDOCS",
    },
  },
};

export const TRNAC: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNAC",
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    docs: {
      MASSID: {},
      FOSTERPLACEMENT: {},
    },
  },
};

// approve all the way
export const TRNAD: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNAD",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    reduced_leave_spec: "0,240,240,240,240,240,0",
    pregnant_or_recent_birth: true,
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
    },
  },
};

export const TRNAE: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNAE",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    reduced_leave_spec: "0,240,240,240,240,240,0",
    pregnant_or_recent_birth: true,
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
  },
};
