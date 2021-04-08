import { parseISO } from "date-fns";
import { ScenarioSpecification } from "../generation/Scenario";

// Cases drawn from: https://docs.google.com/spreadsheets/d/1eb0bzZsfgRaqesaAX_zg6Ez5vDCGVs4yMeUodIXyrn4/edit#gid=0

const start = parseISO("2021-03-15");
const end = parseISO("2021-05-15");
const retroactiveStart = parseISO("2021-02-01");
const retroactiveEnd = parseISO("2021-03-31");

// Happy Path - Employee A: Bonding, Check payment
export const PMTA: ScenarioSpecification = {
  employee: { wages: 90000 },
  claim: {
    label: "PMTA",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    has_continuous_leave_periods: true,
    leave_dates: [start, end],
    address: {
      city: "Boston",
      line_1: "30 Coolidge Rd",
      state: "MA",
      zip: "02134",
    },
    payment: {
      payment_method: "Check",
      bank_account_type: "Checking",
    },
    bondingDate: "past",
    docs: {
      MASSID: {},
      BIRTHCERTIFICATE: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    metadata: { postSubmit: "APPROVE" },
  },
};

// Happy Path - EmployeeB: Medical, Check payment
export const PMTB: ScenarioSpecification = {
  employee: { wages: 60000 },
  claim: {
    label: "PMTB",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: [start, end],
    address: {
      city: "Quincy",
      line_1: "47 Washington St",
      state: "MA",
      zip: "02169",
    },
    payment: {
      payment_method: "Check",
      bank_account_type: "Checking",
    },
    docs: {
      HCP: {},
      MASSID: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    metadata: { postSubmit: "APPROVE" },
  },
};

// Happy Path - EmployeeC: Bonding, deposit payment
export const PMTC: ScenarioSpecification = {
  employee: { wages: 30000 },
  claim: {
    label: "PMTC",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    has_continuous_leave_periods: true,
    leave_dates: [start, end],
    address: {
      city: "Salem",
      line_1: "2 Margin St",
      state: "MA",
      zip: "01970",
    },
    payment: {
      payment_method: "Elec Funds Transfer",
      account_number: "5555555555",
      routing_number: "121042882",
      bank_account_type: "Savings",
    },
    bondingDate: "past",
    docs: {
      MASSID: {},
      BIRTHCERTIFICATE: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    metadata: { postSubmit: "APPROVE" },
  },
};

// Happy Path - EmployeeD: Medical, deposit payment
export const PMTD: ScenarioSpecification = {
  employee: { wages: 90000 },
  claim: {
    label: "PMTD",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: [start, end],
    address: {
      city: "Worcester",
      line_1: "484 Main St",
      state: "MA",
      zip: "01608",
    },
    payment: {
      payment_method: "Elec Funds Transfer",
      account_number: "5555555555",
      routing_number: "121042882",
      bank_account_type: "Savings",
    },
    docs: {
      HCP: {},
      MASSID: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    metadata: { postSubmit: "APPROVE" },
  },
};

// Happy Path - Employee A: Bonding, Check payment
export const PMTE: ScenarioSpecification = {
  employee: { wages: 90000 },
  claim: {
    label: "PMTE",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    has_continuous_leave_periods: true,
    leave_dates: [start, end],
    address: {
      city: "Boston",
      line_1: "30 Coolidge Rd",
      state: "MA",
      zip: "02134",
    },
    payment: {
      payment_method: "Check",
      bank_account_type: "Checking",
    },
    bondingDate: "past",
    docs: {
      MASSID: {},
      BIRTHCERTIFICATE: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    metadata: { postSubmit: "APPROVE" },
  },
};

// Happy Path - EmployeeB: Medical, Check payment
export const PMTF: ScenarioSpecification = {
  employee: { wages: 60000 },
  claim: {
    label: "PMTF",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: [start, end],
    address: {
      city: "Quincy",
      line_1: "47 Washington St",
      state: "MA",
      zip: "02169",
    },
    payment: {
      payment_method: "Check",
      bank_account_type: "Checking",
    },
    docs: {
      HCP: {},
      MASSID: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    metadata: { postSubmit: "APPROVE" },
  },
};

// Happy Path - EmployeeC: Bonding, deposit payment
export const PMTG: ScenarioSpecification = {
  employee: { wages: 30000 },
  claim: {
    label: "PMTG",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    has_continuous_leave_periods: true,
    leave_dates: [start, end],
    address: {
      city: "Salem",
      line_1: "2 Margin St",
      state: "MA",
      zip: "01970",
    },
    payment: {
      payment_method: "Elec Funds Transfer",
      account_number: "5555555555",
      routing_number: "121042882",
      bank_account_type: "Savings",
    },
    bondingDate: "past",
    docs: {
      MASSID: {},
      BIRTHCERTIFICATE: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    metadata: { postSubmit: "APPROVE" },
  },
};

// Happy Path - EmployeeD: Medical, deposit payment
export const PMTH: ScenarioSpecification = {
  employee: { wages: 90000 },
  claim: {
    label: "PMTH",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: [start, end],
    address: {
      city: "Worcester",
      line_1: "484 Main St",
      state: "MA",
      zip: "01608",
    },
    payment: {
      payment_method: "Elec Funds Transfer",
      account_number: "5555555555",
      routing_number: "121042882",
      bank_account_type: "Savings",
    },
    docs: {
      HCP: {},
      MASSID: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    metadata: { postSubmit: "APPROVE" },
  },
};

// Retroactive tests

// Happy Path: Retroactive - Employee A: Bonding, Check payment
export const PMTI: ScenarioSpecification = {
  employee: { wages: 90000 },
  claim: {
    label: "PMTI",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    has_continuous_leave_periods: true,
    leave_dates: [retroactiveStart, retroactiveEnd],
    address: {
      city: "Boston",
      line_1: "30 Coolidge Rd",
      state: "MA",
      zip: "02134",
    },
    payment: {
      payment_method: "Check",
      bank_account_type: "Checking",
    },
    bondingDate: "past",
    docs: {
      MASSID: {},
      BIRTHCERTIFICATE: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    metadata: { postSubmit: "APPROVE" },
  },
};

// Happy Path: Retroactive - EmployeeB: Medical, Check payment
export const PMTJ: ScenarioSpecification = {
  employee: { wages: 60000 },
  claim: {
    label: "PMTJ",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: [retroactiveStart, retroactiveEnd],
    address: {
      city: "Quincy",
      line_1: "47 Washington St",
      state: "MA",
      zip: "02169",
    },
    payment: {
      payment_method: "Check",
      bank_account_type: "Checking",
    },
    docs: {
      HCP: {},
      MASSID: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    metadata: { postSubmit: "APPROVE" },
  },
};

// Happy Path: Retroactive - EmployeeC: Bonding, check payment
export const PMTK: ScenarioSpecification = {
  employee: { wages: 30000 },
  claim: {
    label: "PMTK",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    has_continuous_leave_periods: true,
    leave_dates: [retroactiveStart, retroactiveEnd],
    address: {
      city: "Salem",
      line_1: "2 Margin St",
      state: "MA",
      zip: "01970",
    },
    payment: {
      payment_method: "Check",
      bank_account_type: "Checking",
    },
    bondingDate: "past",
    docs: {
      MASSID: {},
      BIRTHCERTIFICATE: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    metadata: { postSubmit: "APPROVE" },
  },
};

//// Happy Path: Retroactive - EmployeeD: Medical, check payment
//export const PMTL = {
//  reason: "Serious Health Condition - Employee",
//  residence: "MA-proofed",
//  has_continuous_leave_periods: true,
//  leave_dates: [retroactiveStart, claimEnd],
//  address: {
//    city: "Worcester",
//    line_1: "484 Main St",
//    state: "MA",
//    zip: "01608",
//  },
//  payment: {
//    payment_method: "Check",
//    account_number: "",
//    routing_number: "",
//    bank_account_type: "Checking",
//  },
//  wages: 90000,
//  docs: {
//    HCP: {},
//    MASSID: {},
//  }
//});
//
//// Happy Path: Retroactive - Employee A: Bonding, Check payment
//export const PMTM = {
//  reason: "Child Bonding",
//  reason_qualifier: "Newborn",
//  residence: "MA-proofed",
//  has_continuous_leave_periods: true,
//  leave_dates: [retroactiveStart, claimEnd],
//  address: {
//    city: "Boston",
//    line_1: "30 Coolidge Rd",
//    state: "MA",
//    zip: "02134",
//  },
//  payment: {
//    payment_method: "Check",
//    account_number: "",
//    routing_number: "",
//    bank_account_type: "Checking",
//  },
//  bondingDate: "past",
//  wages: 90000,
//  docs: {
//    MASSID: {},
//    BIRTHCERTIFICATE: {},
//  },
//});
