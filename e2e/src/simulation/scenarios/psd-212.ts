import { scenario, chance } from "../simulate";
import { parseISO } from "date-fns";

const paidTomorrow = parseISO("2021-01-01");
const claimEnd = parseISO("2021-02-01");

export const A = scenario("A", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "MA-proofed",
  has_continuous_leave_periods: true,
  work_pattern_spec: "0,470,470,470,470,470,0",
  leave_dates: [paidTomorrow, claimEnd],
  address: {
    city: "Boston",
    line_1: "30 Coolidge Rd",
    state: "MA",
    zip: "02134",
  },
  bondingDate: "past",
  wages: 90000,
  docs: {
    MASSID: {},
    BIRTHCERTIFICATE: {},
  },
  employerResponse: {
    hours_worked_per_week: 39.16,
    employer_decision: "Approve",
    fraud: "No",
  },
});

export const B = scenario("B", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  has_continuous_leave_periods: true,
  work_pattern_spec: "0,470,470,470,470,470,0",
  leave_dates: [paidTomorrow, claimEnd],
  address: {
    city: "Boston",
    line_1: "30 Coolidge Rd",
    state: "MA",
    zip: "02134",
  },
  wages: 30000,
  docs: {
    HCP: {},
    MASSID: {},
  },
  employerResponse: {
    hours_worked_per_week: 39.16,
    employer_decision: "Approve",
    fraud: "No",
  },
});

export const C = scenario("C", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "MA-proofed",
  reduced_leave_spec: "0,240,240,240,240,240,0",
  work_pattern_spec: "0,470,470,470,470,470,0",
  leave_dates: [paidTomorrow, claimEnd],
  address: {
    city: "Boston",
    line_1: "30 Coolidge Rd",
    state: "MA",
    zip: "02134",
  },
  bondingDate: "past",
  wages: 90000,
  docs: {
    MASSID: {},
    BIRTHCERTIFICATE: {},
  },
  employerResponse: {
    hours_worked_per_week: 39.16,
    employer_decision: "Approve",
    fraud: "No",
  },
});

export const D = scenario("D", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  reduced_leave_spec: "0,240,240,240,240,240,0",
  work_pattern_spec: "0,470,470,470,470,470,0",
  leave_dates: [paidTomorrow, claimEnd],
  address: {
    city: "Boston",
    line_1: "30 Coolidge Rd",
    state: "MA",
    zip: "02134",
  },
  wages: 30000,
  docs: {
    HCP: {},
    MASSID: {},
  },
  employerResponse: {
    hours_worked_per_week: 39.16,
    employer_decision: "Approve",
    fraud: "No",
  },
});

export const E = scenario("E", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "MA-proofed",
  reduced_leave_spec: "0,250,250,250,250,250,0",
  work_pattern_spec: "0,470,470,470,470,470,0",
  leave_dates: [paidTomorrow, claimEnd],
  address: {
    city: "Boston",
    line_1: "30 Coolidge Rd",
    state: "MA",
    zip: "02134",
  },
  wages: 90000,
  docs: {
    MASSID: {},
    BIRTHCERTIFICATE: {},
  },
  employerResponse: {
    hours_worked_per_week: 39.16,
    employer_decision: "Approve",
    fraud: "No",
  },
});

export const F = scenario("F", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  reduced_leave_spec: "0,250,250,250,250,250,0",
  work_pattern_spec: "0,470,470,470,470,470,0",
  leave_dates: [paidTomorrow, claimEnd],
  address: {
    city: "Boston",
    line_1: "30 Coolidge Rd",
    state: "MA",
    zip: "02134",
  },
  wages: 30000,
  docs: {
    HCP: {},
    MASSID: {},
  },
  employerResponse: {
    hours_worked_per_week: 39.16,
    employer_decision: "Approve",
    fraud: "No",
  },
});

export const G = scenario("G", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "MA-proofed",
  reduced_leave_spec: "0,250,250,250,250,250,0",
  work_pattern_spec: "0,480,480,480,480,480,0",
  leave_dates: [paidTomorrow, claimEnd],
  address: {
    city: "Boston",
    line_1: "30 Coolidge Rd",
    state: "MA",
    zip: "02134",
  },
  bondingDate: "past",
  wages: 90000,
  docs: {
    MASSID: {},
    BIRTHCERTIFICATE: {},
  },
  employerResponse: {
    hours_worked_per_week: 39.16,
    employer_decision: "Approve",
    fraud: "No",
  },
});

export const H = scenario("H", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  reduced_leave_spec: "0,250,250,250,250,250,0",
  work_pattern_spec: "0,480,480,480,480,480,0",
  leave_dates: [paidTomorrow, claimEnd],
  address: {
    city: "Boston",
    line_1: "30 Coolidge Rd",
    state: "MA",
    zip: "02134",
  },
  wages: 30000,
  docs: {
    HCP: {},
    MASSID: {},
  },
  employerResponse: {
    hours_worked_per_week: 39.16,
    employer_decision: "Approve",
    fraud: "No",
  },
});

export default chance([
  [20, A],
  [20, B],
  [20, C],
  [20, D],
  [20, E],
  [20, F],
  [20, G],
  [20, H],
]);
