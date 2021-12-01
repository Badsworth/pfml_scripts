import { ScenarioSpecification } from "../generation/Scenario";
import { parseISO, addWeeks } from "date-fns";

const start = parseISO("2021-12-02");
const end = addWeeks(start, 7);

const DEC_LEAVE_DATES: [Date, Date] = [start, end];
const JAN_LEAVE_DATES: [Date, Date] = [addWeeks(start, 5), addWeeks(start, 12)];
const COMPLETED_DATES: [Date, Date] = [
  parseISO("2021-09-15"),
  addWeeks(parseISO("2021-09-15"), 5),
];

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
    leave_dates: COMPLETED_DATES,
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
      postSubmit: "APPROVEDOCSEROPEN",
    },
    leave_dates: DEC_LEAVE_DATES,
  },
};

export const TRNG_JAN: ScenarioSpecification = {
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
      postSubmit: "APPROVEDOCSEROPEN",
    },
    leave_dates: JAN_LEAVE_DATES,
  },
};

export const TRNH: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNH",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: DEC_LEAVE_DATES,
    docs: {
      MASSID: {},
      HCP: {},
    },
    metadata: {
      postSubmit: "APPROVEDOCS",
    },
  },
};

// TRNT through TRNAC are bc that should be approved
export const TRNT: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNT",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    bondingDate: "far-past",
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
    },
    leave_dates: COMPLETED_DATES,
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
      postSubmit: "APPROVEDOCSEROPEN",
    },
    leave_dates: DEC_LEAVE_DATES,
  },
};

export const TRNW_JAN: ScenarioSpecification = {
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
      postSubmit: "APPROVEDOCSEROPEN",
    },
    leave_dates: JAN_LEAVE_DATES,
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
    leave_dates: DEC_LEAVE_DATES,
    metadata: {
      postSubmit: "APPROVEDOCS",
    },
  },
};

export const TRNAJ: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNAJ",
    reason: "Care for a Family Member",
    has_continuous_leave_periods: true,
    leave_dates: DEC_LEAVE_DATES,
    docs: {
      MASSID: {},
      CARING: {},
    },
    metadata: {
      postSubmit: "APPROVEDOCSEROPEN",
    },
    employerResponse: {
      employer_decision: "Approve",
      hours_worked_per_week: 40,
    },
  },
};

export const TRNAJ_JAN: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNAJ",
    reason: "Care for a Family Member",
    has_continuous_leave_periods: true,
    leave_dates: JAN_LEAVE_DATES,
    docs: {
      MASSID: {},
      CARING: {},
    },
    metadata: {
      postSubmit: "APPROVEDOCSEROPEN",
    },
    employerResponse: {
      employer_decision: "Approve",
      hours_worked_per_week: 40,
    },
  },
};

export const TRNAL: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNAL",
    reason: "Care for a Family Member",
    leave_dates: DEC_LEAVE_DATES,
    docs: {
      MASSID: {},
      CARING: {},
    },
    metadata: {
      postSubmit: "APPROVEDOCS",
    },
  },
};

export const TRNAM: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNAM",
    reason: "Care for a Family Member",
    reduced_leave_spec: "0,240,240,240,240,240,0",
    docs: {
      MASSID: {},
      CARING: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    metadata: {
      postSubmit: "APPROVE",
    },
    leave_dates: COMPLETED_DATES,
  },
};
