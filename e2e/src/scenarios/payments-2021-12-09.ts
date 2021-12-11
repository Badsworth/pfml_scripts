import { parseISO } from "date-fns";
import { ScenarioSpecification } from "generation/Scenario";
import * as paymentScenarios from "./payments-2021-04-02";

const startJan = parseISO("2022-01-04");
const endJan = parseISO("2022-02-18");

const startDec = parseISO("2021-12-17");
const endDec = parseISO("2022-02-11");

const startMidJan = parseISO("2022-01-17");
const endMidJan = parseISO("2022-02-18");

const leavePeriodOpts: [Date, Date][] = [
  [startMidJan, endMidJan],
  [startJan, endJan],
  [startDec, endDec],
];

const scenarios = [
  "PMT1",
  "PMT2",
  "PMT3",
  "PMT4",
  "PMT5",
  "PMT6",
  "PMT7",
  "PRENOTE1",
  "PRENOTE5",
  "ADDRESS1",
  "ADDRESS2",
  "ADDRESS3",
  "ADDRESS5",
  "ADDRESS6",
  "ADDRESS7",
] as const;

export const WITHHOLDING_RETRO: ScenarioSpecification = {
  employee: { wages: 30000, metadata: { prenoted: "no" } },
  claim: {
    label: "WITHHOLDING_RETRO",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: [startMidJan, endMidJan],
    address: {
      city: "Quincy",
      line_1: "47 Washington St",
      state: "MA",
      zip: "02169",
    },
    payment: { payment_method: "Check" },
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    is_withholding_tax: true,
    metadata: { postSubmit: "APPROVE" },
  },
};

let idx = 0;
export default scenarios.map((scenario) => {
  if (idx >= leavePeriodOpts.length) idx = 0;
  paymentScenarios[scenario].claim.leave_dates = leavePeriodOpts[idx];
  paymentScenarios[scenario].claim.is_withholding_tax = true;
  paymentScenarios[scenario].claim.metadata = {
    ...paymentScenarios[scenario].claim.metadata,
    quantity: scenario !== "ADDRESS7" ? 30 : 5,
  };
  idx += 1;
  return paymentScenarios[scenario];
});
