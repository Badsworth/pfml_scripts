import { scenario, chance } from "../simulate";

// Cases drawn from: https://docs.google.com/spreadsheets/d/1eb0bzZsfgRaqesaAX_zg6Ez5vDCGVs4yMeUodIXyrn4/edit#gid=0

// Happy Path - Employee A: Bonding, Check payment
export const CHAP1 = scenario("CHAP1", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "MA-proofed",
  has_continuous_leave_periods: true,
  leave_dates: [new Date("2020-12-28"), new Date("2020-02-01")],
  address: {
    city: "",
    line_1: "",
    state: "",
    zip: "",
  },
  payment: {
    payment_method: "Check",
    account_number: "",
    routing_number: "",
    bank_account_type: "Checking",
  },
  bondingDate: "past",
  docs: {},
});

// Happy Path - EmployeeB: Medical, Check payment
export const CHAP2 = scenario("CHAP2", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  has_continuous_leave_periods: true,
  leave_dates: [new Date("2020-12-28"), new Date("2020-02-01")],
  address: {
    city: "",
    line_1: "",
    state: "",
    zip: "",
  },
  payment: {
    payment_method: "Check",
    account_number: "",
    routing_number: "",
    bank_account_type: "Checking",
  },
  docs: {},
});

// Happy Path - EmployeeC: Bonding, deposit payment
export const CHAP3 = scenario("CHAP3", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "MA-proofed",
  has_continuous_leave_periods: true,
  leave_dates: [new Date("2020-12-28"), new Date("2020-02-01")],
  address: {
    city: "",
    line_1: "",
    state: "",
    zip: "",
  },
  payment: {
    payment_method: "Debit",
    account_number: "",
    routing_number: "121042882",
    bank_account_type: "Savings",
  },
  bondingDate: "past",
  docs: {},
});

// Happy Path - EmployeeD: Medical, deposit payment
export const CHAP4 = scenario("CHAP4", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  has_continuous_leave_periods: true,
  leave_dates: [new Date("2020-12-28"), new Date("2020-02-01")],
  address: {
    city: "",
    line_1: "",
    state: "",
    zip: "",
  },
  payment: {
    payment_method: "Debit",
    account_number: "",
    routing_number: "121042882",
    bank_account_type: "Savings",
  },
  docs: {},
});

const CHAP = chance([
  [1, CHAP1],
  [1, CHAP2],
  [1, CHAP3],
  [1, CHAP4],
]);

export default chance([[20, CHAP]]);
