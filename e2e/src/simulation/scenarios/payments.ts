import { scenario, chance } from "../simulate";

// Cases drawn from: https://docs.google.com/spreadsheets/d/1eb0bzZsfgRaqesaAX_zg6Ez5vDCGVs4yMeUodIXyrn4/edit#gid=0

// Happy Path - Employee A: Bonding, Check payment
export const PHAP1 = scenario("PHAP1", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "MA-proofed",
  has_continuous_leave_periods: true,
  leave_dates: [new Date("2020-12-28"), new Date("2020-01-07")],
  address: {
    city: "Boston",
    line_1: "30 Coolidge Rd",
    state: "MA",
    zip: "02134",
  },
  payment: {
    payment_method: "Check",
    account_number: "",
    routing_number: "",
    bank_account_type: "Checking",
  },
  bondingDate: "past",
  wages: 90000,
  docs: {},
});

// Happy Path - EmployeeB: Medical, Check payment
export const PHAP2 = scenario("PHAP2", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  has_continuous_leave_periods: true,
  leave_dates: [new Date("2020-12-28"), new Date("2020-01-07")],
  address: {
    city: "Quincy",
    line_1: "47 Washington St",
    state: "MA",
    zip: "02169",
  },
  payment: {
    payment_method: "Check",
    account_number: "",
    routing_number: "",
    bank_account_type: "Checking",
  },
  wages: 60000,
  docs: {},
});

// Happy Path - EmployeeC: Bonding, deposit payment
export const PHAP3 = scenario("PHAP3", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "MA-proofed",
  has_continuous_leave_periods: true,
  leave_dates: [new Date("2020-12-28"), new Date("2020-01-07")],
  address: {
    city: "Salem",
    line_1: "2 Margin St",
    state: "MA",
    zip: "01970",
  },
  payment: {
    payment_method: "Debit",
    account_number: "5555555555",
    routing_number: "121042882",
    bank_account_type: "Savings",
  },
  bondingDate: "past",
  wages: 30000,
  docs: {},
});

// Happy Path - EmployeeD: Medical, deposit payment
export const PHAP4 = scenario("PHAP4", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  has_continuous_leave_periods: true,
  leave_dates: [new Date("2020-12-28"), new Date("2020-01-07")],
  address: {
    city: "Worcester",
    line_1: "484 Main St",
    state: "MA",
    zip: "01608",
  },
  payment: {
    payment_method: "Debit",
    account_number: "5555555555",
    routing_number: "121042882",
    bank_account_type: "Savings",
  },
  wages: 90000,
  docs: {},
});

// Happy Path - Employee A: Bonding, Check payment
export const PHAP5 = scenario("PHAP5", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "MA-proofed",
  has_continuous_leave_periods: true,
  leave_dates: [new Date("2020-12-30"), new Date("2020-01-07")],
  address: {
    city: "Boston",
    line_1: "30 Coolidge Rd",
    state: "MA",
    zip: "02134",
  },
  payment: {
    payment_method: "Check",
    account_number: "",
    routing_number: "",
    bank_account_type: "Checking",
  },
  bondingDate: "past",
  wages: 90000,
  docs: {},
});

// Happy Path - EmployeeB: Medical, Check payment
export const PHAP6 = scenario("PHAP6", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  has_continuous_leave_periods: true,
  leave_dates: [new Date("2020-12-30"), new Date("2020-01-07")],
  address: {
    city: "Quincy",
    line_1: "47 Washington St",
    state: "MA",
    zip: "02169",
  },
  payment: {
    payment_method: "Check",
    account_number: "",
    routing_number: "",
    bank_account_type: "Checking",
  },
  wages: 60000,
  docs: {},
});

// Happy Path - EmployeeC: Bonding, deposit payment
export const PHAP7 = scenario("PHAP7", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "MA-proofed",
  has_continuous_leave_periods: true,
  leave_dates: [new Date("2020-12-30"), new Date("2020-01-07")],
  address: {
    city: "Salem",
    line_1: "2 Margin St",
    state: "MA",
    zip: "01970",
  },
  payment: {
    payment_method: "Debit",
    account_number: "5555555555",
    routing_number: "121042882",
    bank_account_type: "Savings",
  },
  bondingDate: "past",
  wages: 30000,
  docs: {},
});

// Happy Path - EmployeeD: Medical, deposit payment
export const PHAP8 = scenario("PHAP8", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  has_continuous_leave_periods: true,
  leave_dates: [new Date("2020-12-30"), new Date("2020-01-07")],
  address: {
    city: "Worcester",
    line_1: "484 Main St",
    state: "MA",
    zip: "01608",
  },
  payment: {
    payment_method: "Debit",
    account_number: "5555555555",
    routing_number: "121042882",
    bank_account_type: "Savings",
  },
  wages: 90000,
  docs: {},
});

// Retroactive tests

//// Happy Path: Retroactive - Employee A: Bonding, Check payment
//export const RHAP1 = scenario("RHAP1", {
//  reason: "Child Bonding",
//  reason_qualifier: "Newborn",
//  residence: "MA-proofed",
//  has_continuous_leave_periods: true,
//  leave_dates: [new Date("2020-12-01"), new Date("2020-01-08")],
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
//  docs: {},
//});
//
//// Happy Pathi: Retroactive - EmployeeB: Medical, Check payment
//export const RHAP2 = scenario("RHAP2", {
//  reason: "Serious Health Condition - Employee",
//  residence: "MA-proofed",
//  has_continuous_leave_periods: true,
//  leave_dates: [new Date("2020-12-01"), new Date("2020-01-11")],
//  address: {
//    city: "Quincy",
//    line_1: "47 Washington St",
//    state: "MA",
//    zip: "02169",
//  },
//  payment: {
//    payment_method: "Check",
//    account_number: "",
//    routing_number: "",
//    bank_account_type: "Checking",
//  },
//  wages: 60000,
//  docs: {},
//});
//
//// Happy Path: Retroactive - EmployeeC: Bonding, check payment
//export const RHAP3 = scenario("RHAP3", {
//  reason: "Child Bonding",
//  reason_qualifier: "Newborn",
//  residence: "MA-proofed",
//  has_continuous_leave_periods: true,
//  leave_dates: [new Date("2020-12-01"), new Date("2020-01-12")],
//  address: {
//    city: "Salem",
//    line_1: "2 Margin St",
//    state: "MA",
//    zip: "01970",
//  },
//  payment: {
//    payment_method: "Check",
//    account_number: "",
//    routing_number: "",
//    bank_account_type: "Checking",
//  },
//  bondingDate: "past",
//  wages: 30000,
//  docs: {},
//});
//
//// Happy Path: Retroactive - EmployeeD: Medical, check payment
//export const RHAP4 = scenario("RHAP4", {
//  reason: "Serious Health Condition - Employee",
//  residence: "MA-proofed",
//  has_continuous_leave_periods: true,
//  leave_dates: [new Date("2020-12-01"), new Date("2020-01-13")],
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
//  docs: {},
//});
//
//// Happy Path: Retroactive - Employee A: Bonding, Check payment
//export const RHAP5 = scenario("RHAP5", {
//  reason: "Child Bonding",
//  reason_qualifier: "Newborn",
//  residence: "MA-proofed",
//  has_continuous_leave_periods: true,
//  leave_dates: [new Date("2020-12-01"), new Date("2020-01-14")],
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
//  docs: {},
//});

const PHAP = chance([
  [1, PHAP1],
  [1, PHAP2],
  [1, PHAP3],
  [1, PHAP4],
  [1, PHAP5],
  [1, PHAP6],
  [1, PHAP7],
  [1, PHAP8],
]);

export default chance([[20, PHAP]]);
