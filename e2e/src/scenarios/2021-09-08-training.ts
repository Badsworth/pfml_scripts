import { ScenarioSpecification } from "../generation/Scenario";
import { parseISO, addDays, addWeeks } from "date-fns";

const getRandomNumber = (min: number, max: number) => {
  return Math.floor(Math.random() * (max - min + 1)) + min;
};

const randomDay = () => {
  return getRandomNumber(0, 60);
};

const randomWeeksLeave = () => {
  return getRandomNumber(4, 12);
};

const generateLeaveDates = (): [Date, Date] => {
  const start = addDays(parseISO("2021-08-01"), randomDay());
  const end = addWeeks(start, randomWeeksLeave());
  return [start, end];
};

const firstOfMonthStartMaxLeave = (): [Date, Date] => {
  const options = ["2021-09-01", "2021-10-01", "2021-11-01"] as const;
  const selected = options[Math.floor(Math.random() * options.length)];
  return [parseISO(selected), addWeeks(parseISO(selected), 20)];
};

const GENERATE_LEAVE_DATES_DESCRIPTION =
  "Leave begins between 8/1 - 10/1\nEnds 4-12 weeks after start date";

const FIRST_OF_MONTH_START_MAX_LEAVE_DESCRIPTION =
  "Begins 9/1, 10/1, or 11/1\nEnd 20 weeks after start";

// Deny claim for financial eligibility
export const TRNA: ScenarioSpecification = {
  employee: { mass_id: true, wages: "ineligible" },
  claim: {
    label: "TRNA",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    reduced_leave_spec: "0,240,240,240,240,240,0",
    leave_dates: () => generateLeaveDates(),
    docs: {
      // MASSID: {},
      // HCP: {},
    },
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
    leave_dates: () => generateLeaveDates(),
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
    leave_dates: () => generateLeaveDates(),
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
    metadata: {
      postSubmit: "APPROVE",
      leaveDescription: FIRST_OF_MONTH_START_MAX_LEAVE_DESCRIPTION,
      quantity: 100,
    },
    leave_dates: () => firstOfMonthStartMaxLeave(),
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
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 150,
    },
    leave_dates: () => generateLeaveDates(),
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
    leave_dates: () => generateLeaveDates(),
  },
};

export const TRNH: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNH",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: () => generateLeaveDates(),
    docs: {
      MASSID: {},
      HCP: {},
    },
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
    leave_dates: () => firstOfMonthStartMaxLeave(),
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    metadata: {
      postSubmit: "APPROVE",
      leaveDescription: FIRST_OF_MONTH_START_MAX_LEAVE_DESCRIPTION,
      quantity: 100,
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
    metadata: {
      postSubmit: "APPROVEDOCSEROPEN",
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 100,
    },
    leave_dates: () => generateLeaveDates(),
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
    leave_dates: () => generateLeaveDates(),
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
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    metadata: {
      postSubmit: "APPROVEDOCSEROPEN",
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 100,
    },
    leave_dates: () => generateLeaveDates(),
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
    leave_dates: () => generateLeaveDates(),
    metadata: {
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      postSubmit: "APPROVEDOCSEROPEN",
      quantity: 100,
    },
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
    metadata: {
      postSubmit: "APPROVE",
      leaveDescription: FIRST_OF_MONTH_START_MAX_LEAVE_DESCRIPTION,
      quantity: 100,
    },
    leave_dates: () => firstOfMonthStartMaxLeave(),
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
    leave_dates: () => generateLeaveDates(),
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
    docs: {
      // MASSID: {},
      // FOSTERPLACEMENT: {},
    },
    leave_dates: () => generateLeaveDates(),
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
      quantity: 100,
    },
    leave_dates: () => firstOfMonthStartMaxLeave(),
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
    leave_dates: () => generateLeaveDates(),
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
      leaveDescription: GENERATE_LEAVE_DATES_DESCRIPTION,
      quantity: 150,
    },
    leave_dates: () => generateLeaveDates(),
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
    leave_dates: () => generateLeaveDates(),
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
      quantity: 100,
    },
    leave_dates: () => firstOfMonthStartMaxLeave(),
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
      quantity: 200,
    },
    leave_dates: () => generateLeaveDates(),
  },
};

export const TRNAC: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNAC",
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    reduced_leave_spec: "0,240,240,240,240,240,0",
    docs: {
      MASSID: {},
      FOSTERPLACEMENT: {},
    },
    leave_dates: () => generateLeaveDates(),
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
      PREGNANCY_MATERNITY_FORM: {},
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
    leave_dates: () => firstOfMonthStartMaxLeave(),
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
      PREGNANCY_MATERNITY_FORM: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    leave_dates: () => generateLeaveDates(),
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
    work_pattern_spec: "standard",
    leave_dates: () => generateLeaveDates(),
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
      quantity: 100,
    },
    leave_dates: () => firstOfMonthStartMaxLeave(),
  },
};

export const TRNAJ: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNAJ",
    reason: "Care for a Family Member",
    has_continuous_leave_periods: true,
    leave_dates: () => generateLeaveDates(),
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
    has_continuous_leave_periods: true,
    leave_dates: () => generateLeaveDates(),
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
    leave_dates: () => generateLeaveDates(),
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
      quantity: 100,
    },
    leave_dates: () => firstOfMonthStartMaxLeave(),
  },
};

export const TRNAO: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNAO",
    reason: "Care for a Family Member",
    reduced_leave_spec: "0,240,240,240,240,240,0",
    leave_dates: () => generateLeaveDates(),
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
    leave_dates: () => generateLeaveDates(),
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
    leave_dates: () => generateLeaveDates(),
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

export const TRNAS: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNAS",
    has_continuous_leave_periods: true,
    reason: "Care for a Family Member",
    leave_dates: () => generateLeaveDates(),
    docs: {
      MASSID: {},
      CARING: {},
    },
    employerResponse: {
      employer_decision: "Approve",
      hours_worked_per_week: 40,
    },
    metadata: {
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
      quantity: 100,
    },
    leave_dates: () => firstOfMonthStartMaxLeave(),
  },
};

export const TRNOI1: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNOI1",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2021-09-01"), parseISO("2021-11-01")],
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
        income_start_date: "2021-09-01",
        income_end_date: "2021-10-01",
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
    leave_dates: [parseISO("2021-08-01"), parseISO("2021-09-15")],
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
        benefit_start_date: "2021-08-02",
        benefit_end_date: "2021-09-15",
        benefit_amount_dollars: 100,
        benefit_amount_frequency: "Per Week",
        is_full_salary_continuous: false,
      },
    ],
    metadata: {
      postSubmit: "APPROVEDOCS",
      quantity: 2,
    },
  },
};

export const TRNOI3: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNOI3",
    reason: "Pregnancy/Maternity",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2021-10-01"), parseISO("2021-12-01")],
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
    leave_dates: [parseISO("2021-09-01"), parseISO("2021-11-01")],
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
    employer_benefits: [
      {
        benefit_type: "Short-term disability insurance",
        benefit_start_date: "2021-09-01",
        benefit_end_date: "2021-10-01",
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
    leave_dates: [parseISO("2021-09-01"), parseISO("2021-11-15")],
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
    concurrent_leave: {
      is_for_current_employer: true,
      leave_start_date: "2021-08-01",
      leave_end_date: "2021-08-30",
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
    bondingDate: "past",
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
    leave_dates: [parseISO("2021-08-15"), parseISO("2021-11-01")],
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
      leave_start_date: "2021-07-01",
      leave_end_date: "2021-08-01",
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
    leave_dates: [parseISO("2021-09-01"), parseISO("2021-11-01")],
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
          leave_start_date: "2021-05-01",
          leave_end_date: "2021-06-01",
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
    leave_dates: [parseISO("2021-09-01"), parseISO("2021-11-01")],
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
          leave_start_date: "2021-05-01",
          leave_end_date: "2021-06-01",
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
    reason: "Care for a Family Member",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2021-09-15"), parseISO("2021-11-01")],
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
          benefit_start_date: "2021-09-01",
          benefit_end_date: "2021-09-15",
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
    leave_dates: [parseISO("2021-09-15"), parseISO("2021-11-01")],
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
          benefit_start_date: "2021-09-01",
          benefit_end_date: "2021-09-15",
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
    leave_dates: [parseISO("2021-09-01"), parseISO("2021-11-01")],
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
        leave_start_date: "2021-09-01",
        leave_end_date: "2021-09-08",
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
    leave_dates: [parseISO("2021-09-01"), parseISO("2021-11-01")],
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
        leave_start_date: "2021-09-01",
        leave_end_date: "2021-09-08",
      },
    },
    metadata: {
      postSubmit: "APPROVEDOCSEROPEN",
      quantity: 100,
    },
  },
};

export const TRNER4: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNER4",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2021-09-01"), parseISO("2021-11-01")],
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      has_amendments: true,
      employer_decision: "Approve",
      fraud: "No",
      hours_worked_per_week: 40,
      leave_reason: "Serious Health Condition - Employee",
      previous_leaves: [
        {
          leave_reason: "An illness or injury",
          leave_start_date: "2021-05-01",
          leave_end_date: "2021-06-01",
          worked_per_week_minutes: 2250,
        },
      ],
      employer_benefits: [
        {
          benefit_type: "Short-term disability insurance",
          benefit_start_date: "2021-09-01",
          benefit_end_date: "2021-09-15",
          is_full_salary_continuous: false,
          benefit_amount_dollars: 50,
          benefit_amount_frequency: "Per Week",
        },
      ],
    },
    metadata: {
      postSubmit: "APPROVEDOCS",
      quantity: 50,
    },
  },
};

export const TRNER4B: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "TRNER4",
    reason: "Serious Health Condition - Employee",
    work_pattern_spec: "standard",
    leave_dates: [parseISO("2021-09-01"), parseISO("2021-11-01")],
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      has_amendments: true,
      employer_decision: "Approve",
      fraud: "No",
      hours_worked_per_week: 40,
      leave_reason: "Serious Health Condition - Employee",
      previous_leaves: [
        {
          leave_reason: "An illness or injury",
          leave_start_date: "2021-05-01",
          leave_end_date: "2021-06-01",
          worked_per_week_minutes: 2250,
        },
      ],
      employer_benefits: [
        {
          benefit_type: "Short-term disability insurance",
          benefit_start_date: "2021-09-01",
          benefit_end_date: "2021-09-15",
          is_full_salary_continuous: false,
          benefit_amount_dollars: 50,
          benefit_amount_frequency: "Per Week",
        },
      ],
    },
    metadata: {
      postSubmit: "APPROVEDOCSEROPEN",
      quantity: 100,
    },
  },
};
