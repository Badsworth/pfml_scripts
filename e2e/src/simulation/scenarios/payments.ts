import { scenario, chance } from "../simulate";
import { parseISO } from "date-fns";

// Cases drawn from: https://docs.google.com/spreadsheets/d/1eb0bzZsfgRaqesaAX_zg6Ez5vDCGVs4yMeUodIXyrn4/edit#gid=0

const paidTomorrow = parseISO("2021-01-01");
const claimEnd = parseISO("2021-02-01");
const retroactiveStart = parseISO("2020-12-01");

// Happy Path - Employee A: Bonding, Check payment
export const A = scenario("A", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "MA-proofed",
  has_continuous_leave_periods: true,
  leave_dates: [paidTomorrow, claimEnd],
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
  wages: 90000,
  docs: {
    MASSID: {},
    BIRTHCERTIFICATE: {},
  },
  employerResponse: {
    hours_worked_per_week: 40,
    employer_decision: "Approve",
    fraud: "No",
  },
});

// Happy Path - EmployeeB: Medical, Check payment
export const B = scenario("B", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  has_continuous_leave_periods: true,
  leave_dates: [paidTomorrow, claimEnd],
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
  wages: 60000,
  docs: {
    HCP: {},
    MASSID: {},
  },
  employerResponse: {
    hours_worked_per_week: 40,
    employer_decision: "Approve",
    fraud: "No",
  },
});

// Happy Path - EmployeeC: Bonding, deposit payment
export const C = scenario("C", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "MA-proofed",
  has_continuous_leave_periods: true,
  leave_dates: [paidTomorrow, claimEnd],
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
  wages: 30000,
  docs: {
    MASSID: {},
    BIRTHCERTIFICATE: {},
  },
  employerResponse: {
    hours_worked_per_week: 40,
    employer_decision: "Approve",
    fraud: "No",
  },
});

// Happy Path - EmployeeD: Medical, deposit payment
export const D = scenario("D", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  has_continuous_leave_periods: true,
  leave_dates: [paidTomorrow, claimEnd],
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
  wages: 90000,
  docs: {
    HCP: {},
    MASSID: {},
  },
  employerResponse: {
    hours_worked_per_week: 40,
    employer_decision: "Approve",
    fraud: "No",
  },
});

// Happy Path - Employee A: Bonding, Check payment
export const E = scenario("E", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "MA-proofed",
  has_continuous_leave_periods: true,
  leave_dates: [paidTomorrow, claimEnd],
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
  wages: 90000,
  docs: {
    MASSID: {},
    BIRTHCERTIFICATE: {},
  },
  employerResponse: {
    hours_worked_per_week: 40,
    employer_decision: "Approve",
    fraud: "No",
  },
});

// Happy Path - EmployeeB: Medical, Check payment
export const F = scenario("F", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  has_continuous_leave_periods: true,
  leave_dates: [paidTomorrow, claimEnd],
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
  wages: 60000,
  docs: {
    HCP: {},
    MASSID: {},
  },
  employerResponse: {
    hours_worked_per_week: 40,
    employer_decision: "Approve",
    fraud: "No",
  },
});

// Happy Path - EmployeeC: Bonding, deposit payment
export const G = scenario("G", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "MA-proofed",
  has_continuous_leave_periods: true,
  leave_dates: [paidTomorrow, claimEnd],
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
  wages: 30000,
  docs: {
    MASSID: {},
    BIRTHCERTIFICATE: {},
  },
  employerResponse: {
    hours_worked_per_week: 40,
    employer_decision: "Approve",
    fraud: "No",
  },
});

// Happy Path - EmployeeD: Medical, deposit payment
export const H = scenario("H", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  has_continuous_leave_periods: true,
  leave_dates: [paidTomorrow, claimEnd],
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
  wages: 90000,
  docs: {
    HCP: {},
    MASSID: {},
  },
  employerResponse: {
    hours_worked_per_week: 40,
    employer_decision: "Approve",
    fraud: "No",
  },
});

// Retroactive tests

// Happy Path: Retroactive - Employee A: Bonding, Check payment
export const I = scenario("I", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "MA-proofed",
  has_continuous_leave_periods: true,
  leave_dates: [retroactiveStart, claimEnd],
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
  wages: 90000,
  docs: {
    MASSID: {},
    BIRTHCERTIFICATE: {},
  },
  employerResponse: {
    hours_worked_per_week: 40,
    employer_decision: "Approve",
    fraud: "No",
  },
});

// Happy Pathi: Retroactive - EmployeeB: Medical, Check payment
export const J = scenario("J", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  has_continuous_leave_periods: true,
  leave_dates: [retroactiveStart, claimEnd],
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
  wages: 60000,
  docs: {
    HCP: {},
    MASSID: {},
  },
  employerResponse: {
    hours_worked_per_week: 40,
    employer_decision: "Approve",
    fraud: "No",
  },
});

// Happy Path: Retroactive - EmployeeC: Bonding, check payment
export const K = scenario("K", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "MA-proofed",
  has_continuous_leave_periods: true,
  leave_dates: [retroactiveStart, claimEnd],
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
  wages: 30000,
  docs: {
    MASSID: {},
    BIRTHCERTIFICATE: {},
  },
  employerResponse: {
    hours_worked_per_week: 40,
    employer_decision: "Approve",
    fraud: "No",
  },
});

//// Happy Path: Retroactive - EmployeeD: Medical, check payment
//export const L = scenario("L", {
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
//export const M = scenario("M", {
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

export default chance([
  [20, A],
  [20, B],
  [20, C],
  [20, D],
  // [20, E],
  // [20, F],
  // [20, G],
  // [20, H],
  [1, I],
  [1, J],
  [1, K],
]);
