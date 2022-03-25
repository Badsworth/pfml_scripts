import { ScenarioSpecification } from "../generation/Scenario";
import { parseISO } from "date-fns";

export const PORTAL_PREGNANCY_POSTNATAL_DISABLIITY_CONTINUOUS: ScenarioSpecification =
  {
    employee: { mass_id: true, wages: "eligible" },
    claim: {
      label: "PORTAL_PREGNANCY_POSTNATAL_DISABLIITY_CONTINUOUS",
      work_pattern_spec: "standard",
      has_continuous_leave_periods: true,
      reason: "Pregnancy/Maternity",
      leave_dates: [parseISO("2022-03-13"), parseISO("2022-05-22")],
      is_withholding_tax: false,
      docs: {
        MASSID: {},
        PREGNANCY_MATERNITY_FORM: {},
      },
      employerResponse: {
        hours_worked_per_week: 40,
        employer_decision: "Approve",
      },
      metadata: {
        amount: 12,
      },
    },
  };

export const PORTAL_PREGNANCY_POSTNATAL_DISABLITITY_REDUCED: ScenarioSpecification =
  {
    employee: { mass_id: true, wages: "eligible" },
    claim: {
      label: "PORTAL_PREGNANCY_POSTNATAL_DISABLITITY_REDUCED",
      reduced_leave_spec: "0, 480, 480, 480, 480, 480, 0",
      reason: "Pregnancy/Maternity",
      leave_dates: [parseISO("2022-03-08"), parseISO("2022-03-25")],
      is_withholding_tax: false,
      docs: {
        MASSID: {},
        PREGNANCY_MATERNITY_FORM: {},
      },
      employerResponse: {
        hours_worked_per_week: 40,
        employer_decision: "Approve",
      },
      metadata: {
        amount: 5,
      },
    },
  };

export const PORTAL_BONDING_ADOPTION_CONTINUOUS_SITFIT: ScenarioSpecification =
  {
    employee: { mass_id: true, wages: "eligible" },
    claim: {
      label: "PORTAL_BONDING_ADOPTION_CONTINUOUS_SITFIT",
      intermittent_leave_spec: {
        duration: 3,
        duration_basis: "Days",
      },
      reason: "Child Bonding",
      reason_qualifier: "Adoption",
      leave_dates: [parseISO("2022-03-13"), parseISO("2022-05-01")],
      is_withholding_tax: true,
      docs: {
        MASSID: {},
        ADOPTIONCERT: {},
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

export const PORTAL_BONDING_FOSTERCARE_REDUCED: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "PORTAL_BONDING_FOSTERCARE_REDUCED_2",
    reduced_leave_spec: "0, 0, 240, 240, 240, 240, 0",
    leave_dates: [parseISO("2022-05-01"), parseISO("2022-07-10")],
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    bondingDate: "future",
    is_withholding_tax: false,
    docs: {
      MASSID: {},
      FOSTERPLACEMENT: {},
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

export const PORTAL_BONDING_NEWBORN_REDUCED_SITFIT: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "PORTAL_BONDING_NEWBORN_REDUCED_SITFIT",
    reduced_leave_spec: "0, 0, 240, 240, 240, 240, 0",
    leave_dates: [parseISO("2022-03-13"), parseISO("2022-05-01")],
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    is_withholding_tax: true,
    docs: {
      MASSID: {},
      BIRTHCERTIFICATE: {},
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

export const PORTAL_SICKNESS_NONSERIOUS_INTERMITTENT: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "PORTAL_SICKNESS_NONSERIOUS_INTERMITTENT",
    intermittent_leave_spec: {
      duration: 3,
      duration_basis: "Days",
    },
    reason: "Care for a Family Member",
    leave_dates: [parseISO("2022-05-11"), parseISO("2022-06-29")],
    is_withholding_tax: false,
    docs: {
      MASSID: {},
      CARING: {},
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

export const PORTAL_SICKNESS_NONSERIOUS_INTERMITTENT_SITFIT: ScenarioSpecification =
  {
    employee: { mass_id: true, wages: "eligible" },
    claim: {
      label: "PORTAL_SICKNESS_NONSERIOUS_INTERMITTENT_SITFIT",
      intermittent_leave_spec: {
        duration: 3,
        duration_basis: "Days",
      },
      reason: "Care for a Family Member",
      leave_dates: [parseISO("2022-05-11"), parseISO("2022-06-29")],
      is_withholding_tax: true,
      docs: {
        MASSID: {},
        CARING: {},
      },
      employerResponse: {
        hours_worked_per_week: 40,
        employer_decision: "Approve",
      },
      metadata: {
        amount: 12,
      },
    },
  };

export const PORTAL_PREGNANCY_POSTNATAL_DISABLITIY_CONTINUOUS_SITFIT: ScenarioSpecification =
  {
    employee: { mass_id: true, wages: "eligible" },
    claim: {
      label: "PORTAL_PREGNANCY_POSTNATAL_DISABLITIY_CONTINUOUS_SITFIT",
      work_pattern_spec: "standard",
      has_continuous_leave_periods: true,
      reason: "Pregnancy/Maternity",
      leave_dates: [parseISO("2022-04-01"), parseISO("2022-06-29")],
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
        amount: 20,
      },
    },
  };

export const PORTAL_BONDING_FOSTERCARE_REDUCED_2: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "PORTAL_BONDING_FOSTERCARE_REDUCED_2",
    reduced_leave_spec: "0, 240, 240, 240, 240, 240, 0",
    leave_dates: [parseISO("2022-05-23"), parseISO("2022-08-08")],
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    bondingDate: "future",
    is_withholding_tax: false,
    docs: {
      MASSID: {},
      FOSTERPLACEMENT: {},
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

export const PORTAL_CARING_SERIOUSHEALTH_CONTINUOUS: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "PORTAL_CARING_SERIOUSHEALTH_CONTINUOUS",
    work_pattern_spec: "standard",
    has_continuous_leave_periods: true,
    reason: "Care for a Family Member",
    leave_dates: [parseISO("2022-05-23"), parseISO("2022-08-08")],
    is_withholding_tax: false,
    docs: {
      MASSID: {},
      CARING: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    metadata: {
      postSubmit: "APPROVEDOCS",
      amount: 15,
    },
  },
};

export const PERF_APRIL_A: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "PERF_APRIL_A",
    work_pattern_spec: "standard",
    has_continuous_leave_periods: true,
    reason: "Serious Health Condition - Employee",
    leave_dates: [parseISO("2022-02-06"), parseISO("2022-03-25")],
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
    leave_dates: [parseISO("2022-03-23"), parseISO("2022-05-17")],
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
    leave_dates: [parseISO("2022-04-17"), parseISO("2022-05-09")],
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
    leave_dates: [parseISO("2022-03-27"), parseISO("2022-05-15")],
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
    leave_dates: [parseISO("2022-03-20"), parseISO("2022-06-05")],
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
    leave_dates: [parseISO("2022-03-25"), parseISO("2022-05-17")],
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
    leave_dates: [parseISO("2022-04-17"), parseISO("2022-05-29")],
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
    leave_dates: [parseISO("2022-03-27"), parseISO("2022-06-22")],
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
