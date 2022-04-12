// This file contains the scenarios used to generate claims used for training and trn refreshes
// These scenarios remain the same for the most part with the exception being the leave dates.

import { ScenarioSpecification } from "../generation/Scenario";
import { parseISO, addWeeks, subDays, addDays } from "date-fns";
import faker from "faker";
const getRandomNumber = (min: number, max: number) => {
  return Math.floor(Math.random() * (max - min + 1)) + min;
};

const randomWeeksLeave = () => {
  return getRandomNumber(4, 12);
};

const generateRandomLeave = (): [Date, Date] => {
  const start = faker.date.between(
    parseISO("2022-05-01"),
    addDays(new Date(), 60)
  );
  const end = addWeeks(start, randomWeeksLeave());
  return [start, end];
};

const generateMaxLeave = (maxLeaveLength: 20 | 12): [Date, Date] => {
  const start = faker.date.between(
    parseISO("2022-05-01"),
    addDays(new Date(), 60)
  );
  const end = subDays(addWeeks(start, maxLeaveLength), 1);
  return [start, end];
};

const GENERATE_LEAVE_DATES_DESCRIPTION =
  "Leave begins between 05/01/22 - 07/XX/22\nEnds 4-12 weeks after start date";

const FIRST_OF_MONTH_START_MAX_LEAVE_DESCRIPTION =
  "Leave begins between 05/01/22 - 07/XX/22\nMaximum leave length";

// Deny claim for financial eligibility
export const TRNA: ScenarioSpecification = {
  employee: { mass_id: true, wages: "ineligible" },
  claim: {
    label: "TRNA",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    reduced_leave_spec: "0,240,240,240,240,240,0",
    leave_dates: () => generateRandomLeave(),
    docs: {
      // MASSID: {},
      // HCP: {},
    },
    is_withholding_tax: true,
    metadata: {
      postSubmit: "DENY",
      // include leave description here
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 20,
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
    leave_dates: () => generateRandomLeave(),
    is_withholding_tax: true,
    docs: {
      MASSID: { invalid: false },
      HCP: { invalid: true },
    },
    metadata: {
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 80,
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
    leave_dates: () => generateRandomLeave(),
    docs: {
      MASSID: { invalid: true },
      HCP: { invalid: true },
    },
    metadata: {
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 200,
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
    is_withholding_tax: true,
    metadata: {
      postSubmit: "APPROVE",
      leaveDescription: FIRST_OF_MONTH_START_MAX_LEAVE_DESCRIPTION,
      quantity: 200,
    },
    leave_dates: () => generateMaxLeave(20),
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
    is_withholding_tax: true,
    metadata: {
      postSubmit: "APPROVEDOCSEROPEN",
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 150,
    },
    leave_dates: () => generateRandomLeave(),
  },
};

export const TRNG2: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNG2",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    docs: {
      MASSID: {},
      HCP: {},
    },
    metadata: {
      postSubmit: "APPROVEDOCS",
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 150,
    },
    leave_dates: () => generateRandomLeave(),
  },
};

export const TRNH: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNH",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: () => generateRandomLeave(),
    docs: {
      MASSID: {},
      HCP: {},
    },
    is_withholding_tax: true,
    metadata: {
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 300,
    },
  },
};

export const TRNI: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNI",
    reason: "Serious Health Condition - Employee",
    reduced_leave_spec: "0,240,240,240,240,240,0",
    docs: {
      MASSID: {},
      HCP: {},
    },
    leave_dates: () => generateMaxLeave(20),
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    metadata: {
      postSubmit: "APPROVE",
      leaveDescription: FIRST_OF_MONTH_START_MAX_LEAVE_DESCRIPTION,
      quantity: 200,
    },
  },
};

export const TRNL: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNL",
    reason: "Serious Health Condition - Employee",
    reduced_leave_spec: "0,240,240,240,240,240,0",
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    is_withholding_tax: true,
    metadata: {
      postSubmit: "APPROVEDOCSEROPEN",
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 100,
    },
    leave_dates: () => generateRandomLeave(),
  },
};

export const TRNM: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNM",
    reason: "Serious Health Condition - Employee",
    reduced_leave_spec: "0,240,240,240,240,240,0",
    docs: {
      MASSID: {},
      HCP: {},
    },
    leave_dates: () => generateRandomLeave(),
    metadata: {
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 200,
    },
  },
};

export const TRNO: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNO",
    reason: "Serious Health Condition - Employee",
    intermittent_leave_spec: true,
    docs: {
      MASSID: {},
      HCP: {},
    },
    is_withholding_tax: true,
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    metadata: {
      postSubmit: "APPROVEDOCSEROPEN",
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 100,
    },
    leave_dates: () => generateRandomLeave(),
  },
};

// See if it's possible to do intermittent w/ rotating schedule. If it's not possible, we could switch this to continuous leave.
export const TRNQ: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNQ",
    reason: "Serious Health Condition - Employee",
    intermittent_leave_spec: true,
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    is_withholding_tax: true,
    metadata: {
      postSubmit: "APPROVE",
      leaveDescription: FIRST_OF_MONTH_START_MAX_LEAVE_DESCRIPTION,
      quantity: 200,
    },
    leave_dates: () => generateMaxLeave(12),
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
    leave_dates: () => generateRandomLeave(),
    metadata: {
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 80,
    },
  },
};

export const TRNS: ScenarioSpecification = {
  employee: { mass_id: true, wages: "ineligible" },
  claim: {
    label: "TRNS",
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    is_withholding_tax: true,
    docs: {
      // MASSID: {},
      // FOSTERPLACEMENT: {},
    },
    leave_dates: () => generateRandomLeave(),
    metadata: {
      postSubmit: "DENY",
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 20,
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
      leaveDescription: FIRST_OF_MONTH_START_MAX_LEAVE_DESCRIPTION,
      quantity: 200,
    },
    leave_dates: () => generateMaxLeave(12),
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
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 150,
    },
    leave_dates: () => generateRandomLeave(),
  },
};

export const TRNX: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNX",
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    is_withholding_tax: true,
    docs: {
      MASSID: {},
      FOSTERPLACEMENT: {},
    },
    metadata: {
      postSubmit: "APPROVEDOCS",
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 150,
    },
    leave_dates: () => generateRandomLeave(),
  },
};

export const TRNY: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNY",
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    is_withholding_tax: true,
    docs: {
      MASSID: {},
      FOSTERPLACEMENT: {},
    },
    leave_dates: () => generateRandomLeave(),
    metadata: {
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 300,
    },
  },
};

export const TRNZ: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNZ",
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    is_withholding_tax: true,
    reduced_leave_spec: "0,240,240,240,240,240,0",
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
      leaveDescription: FIRST_OF_MONTH_START_MAX_LEAVE_DESCRIPTION,
      quantity: 200,
    },
    leave_dates: () => generateMaxLeave(12),
  },
};

export const TRNAB: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNAB",
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    reduced_leave_spec: "0,240,240,240,240,240,0",
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
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 300,
    },
    leave_dates: () => generateRandomLeave(),
  },
};

export const TRNAC: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNAC",
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    reduced_leave_spec: "0,240,240,240,240,240,0",
    is_withholding_tax: true,
    docs: {
      MASSID: {},
      FOSTERPLACEMENT: {},
    },
    leave_dates: () => generateRandomLeave(),
    metadata: {
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 200,
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
      leaveDescription: FIRST_OF_MONTH_START_MAX_LEAVE_DESCRIPTION,
      quantity: 100,
    },
    leave_dates: () => generateMaxLeave(20),
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
    leave_dates: () => generateRandomLeave(),
    metadata: {
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 100,
    },
  },
};

export const TRNAF: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNAF",
    reason: "Care for a Family Member",
    is_withholding_tax: true,
    work_pattern_spec: "standard",
    leave_dates: () => generateRandomLeave(),
    docs: {
      MASSID: {},
      CARING: { invalid: true },
    },
    metadata: {
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 200,
    },
  },
};

export const TRNAG: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNAG",
    reason: "Care for a Family Member",
    is_withholding_tax: true,
    work_pattern_spec: "standard",
    docs: {
      MASSID: {},
      CARING: {},
    },
    employerResponse: {
      employer_decision: "Approve",
      hours_worked_per_week: 40,
    },
    metadata: {
      postSubmit: "APPROVE",
      leaveDescription: FIRST_OF_MONTH_START_MAX_LEAVE_DESCRIPTION,
      quantity: 200,
    },
    leave_dates: () => generateMaxLeave(12),
  },
};

export const TRNAJ: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNAJ",
    reason: "Care for a Family Member",
    is_withholding_tax: true,
    has_continuous_leave_periods: true,
    leave_dates: () => generateRandomLeave(),
    docs: {
      MASSID: {},
      CARING: {},
    },
    metadata: {
      postSubmit: "APPROVEDOCSEROPEN",
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 150,
    },
    employerResponse: {
      employer_decision: "Approve",
      hours_worked_per_week: 40,
    },
  },
};

export const TRNAK: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNAK",
    reason: "Care for a Family Member",
    is_withholding_tax: true,
    has_continuous_leave_periods: true,
    leave_dates: () => generateRandomLeave(),
    docs: {
      MASSID: {},
      CARING: {},
    },
    metadata: {
      postSubmit: "APPROVEDOCS",
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 150,
    },
  },
};

export const TRNAL: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNAL",
    reason: "Care for a Family Member",
    leave_dates: () => generateRandomLeave(),
    docs: {
      MASSID: {},
      CARING: {},
    },
    metadata: {
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 300,
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
      leaveDescription: FIRST_OF_MONTH_START_MAX_LEAVE_DESCRIPTION,
      quantity: 200,
    },
    leave_dates: () => generateMaxLeave(12),
  },
};

export const TRNAO: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNAO",
    reason: "Care for a Family Member",
    is_withholding_tax: true,
    reduced_leave_spec: "0,240,240,240,240,240,0",
    leave_dates: () => generateRandomLeave(),
    docs: {
      MASSID: {},
      CARING: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    metadata: {
      postSubmit: "APPROVEDOCSEROPEN",
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 100,
    },
  },
};

export const TRNAP: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNAP",
    reason: "Care for a Family Member",
    reduced_leave_spec: "0,240,240,240,240,240,0",
    is_withholding_tax: true,
    leave_dates: () => generateRandomLeave(),
    docs: {
      MASSID: {},
      CARING: {},
    },
    metadata: {
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 200,
    },
  },
};

export const TRNAR: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNAR",
    reason: "Care for a Family Member",
    intermittent_leave_spec: true,
    leave_dates: () => generateRandomLeave(),
    docs: {
      MASSID: {},
      CARING: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    metadata: {
      postSubmit: "APPROVEDOCSEROPEN",
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 100,
    },
  },
};

// The question here is whether we're able to enter the intermittent leave pattern at approval time.  (If yes, should push all the way through approval)
export const TRNAT: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNAT",
    intermittent_leave_spec: true,
    reason: "Care for a Family Member",
    docs: {
      MASSID: {},
      CARING: {},
    },
    employerResponse: {
      employer_decision: "Approve",
      hours_worked_per_week: 40,
    },
    metadata: {
      postSubmit: "APPROVE",
      leaveDescription: FIRST_OF_MONTH_START_MAX_LEAVE_DESCRIPTION,
      quantity: 200,
    },
    leave_dates: () => generateMaxLeave(12),
  },
};

export const TRNOI1: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNOI1",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2022-05-03"), parseISO("2022-07-04")],
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
        income_start_date: "2022-01-03",
        income_end_date: "2022-02-01",
        income_amount_dollars: 500,
        income_amount_frequency: "Per Week",
      },
    ],
    metadata: {
      postSubmit: "APPROVEDOCS",
      quantity: 25,
    },
  },
};

export const TRNOI2: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNOI2",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2022-05-15"), parseISO("2022-06-14")],
    is_withholding_tax: true,
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
        benefit_start_date: "2022-01-15",
        benefit_end_date: "2022-01-31",
        benefit_amount_dollars: 100,
        benefit_amount_frequency: "Per Week",
        is_full_salary_continuous: false,
      },
    ],
    metadata: {
      postSubmit: "APPROVEDOCS",
      quantity: 25,
    },
  },
};

export const TRNOI3: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNOI3",
    reason: "Pregnancy/Maternity",
    work_pattern_spec: "standard",
    is_withholding_tax: true,
    leave_dates: [parseISO("2022-06-14"), parseISO("2022-08-15")],
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
        income_start_date: "2021-10-01",
        income_end_date: "2021-11-01",
        income_amount_dollars: 1000,
        income_amount_frequency: "Per Month",
      },
    ],
    metadata: {
      postSubmit: "APPROVEDOCS",
      quantity: 25,
    },
  },
};

export const TRNOI4: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNOI4",
    reason: "Pregnancy/Maternity",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2022-05-03"), parseISO("2022-07-04")],
    docs: {
      MASSID: {},
      PREGNANCY_MATERNITY_FORM: {},
    },
    is_withholding_tax: true,
    employerResponse: {
      has_amendments: false,
      fraud: "No",
      employer_decision: "Approve",
      hours_worked_per_week: 40,
    },
    employer_benefits: [
      {
        benefit_type: "Short-term disability insurance",
        benefit_start_date: "2022-02-01",
        benefit_end_date: "2022-02-10",
        benefit_amount_dollars: 100,
        benefit_amount_frequency: "Per Month",
        is_full_salary_continuous: false,
      },
    ],
    metadata: {
      postSubmit: "APPROVEDOCS",
      quantity: 25,
    },
  },
};

export const TRNOL1: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNOL1",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2022-05-15"), parseISO("2022-06-14")],
    docs: {
      MASSID: {},
      HCP: {},
    },
    is_withholding_tax: true,
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
        leave_start_date: "2022-01-01",
        leave_end_date: "2022-01-14",
        worked_per_week_minutes: 2400,
        leave_minutes: 2400,
      },
    ],
    metadata: {
      postSubmit: "APPROVEDOCS",
      quantity: 25,
    },
  },
};

export const TRNOL2: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNOL2",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2022-06-14"), parseISO("2022-08-15")],
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
      leave_start_date: "2022-01-01",
      leave_end_date: "2022-02-13",
    },

    metadata: {
      postSubmit: "APPROVEDOCS",
      quantity: 25,
    },
  },
};

export const TRNOL3: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNOL3",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    is_withholding_tax: true,
    bondingDate: "future",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2022-05-24"), parseISO("2022-07-25")],
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
        leave_start_date: "2022-01-01",
        leave_end_date: "2022-01-23",
        worked_per_week_minutes: 2400,
        leave_minutes: 2400,
      },
    ],
    metadata: {
      postSubmit: "APPROVEDOCS",
      quantity: 25,
    },
  },
};

export const TRNOL4: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNOL4",
    reason: "Pregnancy/Maternity",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2022-05-15"), parseISO("2022-06-14")],
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
    concurrent_leave: {
      is_for_current_employer: true,
      leave_start_date: "2022-01-01",
      leave_end_date: "2022-01-14",
    },
    metadata: {
      postSubmit: "APPROVEDOCS",
      quantity: 25,
    },
  },
};

export const TRNER1: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNER1",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    is_withholding_tax: true,
    leave_dates: [parseISO("2022-06-14"), parseISO("2022-08-15")],
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      has_amendments: true,
      fraud: "No",
      employer_decision: "Approve",
      hours_worked_per_week: 37.5,
      leave_reason: "Serious Health Condition - Employee",
      previous_leaves: [
        {
          leave_reason: "An illness or injury",
          type: "same_reason",
          leave_start_date: "2022-01-01",
          leave_end_date: "2022-02-13",
        },
      ],
    },
    metadata: {
      postSubmit: "APPROVEDOCS",
      quantity: 25,
    },
  },
};

export const TRNER1B: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNER1B",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2022-05-03"), parseISO("2022-07-04")],
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      has_amendments: true,
      fraud: "No",
      employer_decision: "Approve",
      hours_worked_per_week: 37.5,
      leave_reason: "Serious Health Condition - Employee",
      previous_leaves: [
        {
          leave_reason: "An illness or injury",
          type: "same_reason",
          leave_start_date: "2022-01-01",
          leave_end_date: "2022-01-02",
        },
      ],
    },
    metadata: {
      postSubmit: "APPROVEDOCSEROPEN",
      quantity: 100,
    },
  },
};

export const TRNER2: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNER2",
    is_withholding_tax: true,
    reason: "Care for a Family Member",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2022-05-15"), parseISO("2022-06-14")],
    docs: {
      MASSID: {},
      CARING: {},
    },
    employerResponse: {
      has_amendments: true,
      fraud: "No",
      employer_decision: "Approve",
      hours_worked_per_week: 40,
      leave_reason: "Care for a Family Member",
      believe_relationship_accurate: "Yes",
      employer_benefits: [
        {
          benefit_type: "Short-term disability insurance",
          benefit_amount_dollars: 50,
          benefit_amount_frequency: "Per Week",
          benefit_start_date: "2022-01-01",
          benefit_end_date: "2022-01-13",
        },
      ],
    },
    metadata: {
      postSubmit: "APPROVEDOCS",
      quantity: 25,
    },
  },
};

export const TRNER2B: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNER2B",
    reason: "Care for a Family Member",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2022-06-14"), parseISO("2022-08-15")],
    docs: {
      MASSID: {},
      CARING: {},
    },
    employerResponse: {
      has_amendments: true,
      fraud: "No",
      employer_decision: "Approve",
      hours_worked_per_week: 40,
      leave_reason: "Care for a Family Member",
      believe_relationship_accurate: "Yes",
      employer_benefits: [
        {
          benefit_type: "Short-term disability insurance",
          benefit_amount_dollars: 50,
          benefit_amount_frequency: "Per Week",
          benefit_start_date: "2022-02-01",
          benefit_end_date: "2022-02-13",
        },
      ],
    },
    metadata: {
      postSubmit: "APPROVEDOCSEROPEN",
      quantity: 100,
    },
  },
};

export const TRNER3: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNER3",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    bondingDate: "past",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2022-05-03"), parseISO("2022-07-04")],
    docs: {
      MASSID: {},
      BIRTHCERTIFICATE: {},
    },
    is_withholding_tax: true,
    employerResponse: {
      has_amendments: true,
      fraud: "No",
      employer_decision: "Approve",
      hours_worked_per_week: 36,
      leave_reason: "Child Bonding",
      concurrent_leave: {
        is_for_current_employer: true,
        leave_start_date: "2022-01-01",
        leave_end_date: "2022-01-14",
      },
    },
    metadata: {
      postSubmit: "APPROVEDOCS",
      quantity: 25,
    },
  },
};

export const TRNER3B: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNER3B",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    bondingDate: "past",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2022-05-15"), parseISO("2022-06-14")],
    docs: {
      MASSID: {},
      BIRTHCERTIFICATE: {},
    },
    employerResponse: {
      has_amendments: true,
      fraud: "No",
      employer_decision: "Approve",
      hours_worked_per_week: 36,
      leave_reason: "Child Bonding",
      concurrent_leave: {
        is_for_current_employer: true,
        leave_start_date: "2022-01-01",
        leave_end_date: "2022-01-14",
      },
    },
    metadata: {
      postSubmit: "APPROVEDOCSEROPEN",
      quantity: 100,
    },
  },
};

// Historical scenarios, not going to be used for the latest data load

// export const TRNER4: ScenarioSpecification = {
//   employee: { mass_id: true, wages: "eligible" },
//   claim: {
//     label: "TRNER4",
//     reason: "Serious Health Condition - Employee",
//     work_pattern_spec: "standard",
//     leave_dates: [parseISO("2021-09-01"), parseISO("2021-11-01")],
//     docs: {
//       MASSID: {},
//       HCP: {},
//     },
//     employerResponse: {
//       has_amendments: true,
//       employer_decision: "Approve",
//       fraud: "No",
//       hours_worked_per_week: 40,
//       leave_reason: "Serious Health Condition - Employee",
//       previous_leaves: [
//         {
//           leave_reason: "An illness or injury",
//           leave_start_date: "2021-05-01",
//           leave_end_date: "2021-06-01",
//           worked_per_week_minutes: 2250,
//         },
//       ],
//       employer_benefits: [
//         {
//           benefit_type: "Short-term disability insurance",
//           benefit_start_date: "2021-09-01",
//           benefit_end_date: "2021-09-15",
//           is_full_salary_continuous: false,
//           benefit_amount_dollars: 50,
//           benefit_amount_frequency: "Per Week",
//         },
//       ],
//     },
//     metadata: {
//       postSubmit: "APPROVEDOCS",
//       quantity: 50,
//     },
//   },
// };

// export const TRNER4B: ScenarioSpecification = {
//   employee: { mass_id: true, wages: "eligible" },
//   claim: {
//     label: "TRNER4",
//     reason: "Serious Health Condition - Employee",
//     work_pattern_spec: "standard",
//     leave_dates: [parseISO("2021-09-01"), parseISO("2021-11-01")],
//     docs: {
//       MASSID: {},
//       HCP: {},
//     },
//     employerResponse: {
//       has_amendments: true,
//       employer_decision: "Approve",
//       fraud: "No",
//       hours_worked_per_week: 40,
//       leave_reason: "Serious Health Condition - Employee",
//       previous_leaves: [
//         {
//           leave_reason: "An illness or injury",
//           leave_start_date: "2021-05-01",
//           leave_end_date: "2021-06-01",
//           worked_per_week_minutes: 2250,
//         },
//       ],
//       employer_benefits: [
//         {
//           benefit_type: "Short-term disability insurance",
//           benefit_start_date: "2021-09-01",
//           benefit_end_date: "2021-09-15",
//           is_full_salary_continuous: false,
//           benefit_amount_dollars: 50,
//           benefit_amount_frequency: "Per Week",
//         },
//       ],
//     },
//     metadata: {
//       postSubmit: "APPROVEDOCSEROPEN",
//       quantity: 100,
//     },
//   },
// };

// NEW for April	Bonding 	BI	TRNAV	Intermittent	Approved	100	"Randomize between start dates beginning 12/27 through 03/01/2022
// Max duration of leave (12 weeks)"
// "1. Add ER task
//  2. Close all tasks
// 3. Approve evidence
// 4. Approve"	Should push all the way through approval
// 100
export const TRNAV: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNAV",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    leave_dates: generateMaxLeave(12),
    bondingDate: "far-past",
    intermittent_leave_spec: true,
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    docs: {
      MASSID: {},
      BIRTHCERTIFICATE: {},
    },
    metadata: {
      postSubmit: "APPROVE",
      quantity: 100,
    },
  },
};
