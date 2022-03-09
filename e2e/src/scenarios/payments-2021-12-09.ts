import { parseISO } from "date-fns";
import * as paymentScenarios from "./payments-2021-04-02";

const start = parseISO("2022-01-04");
const end = parseISO("2022-02-18");

const scenarios = [
  "PMT1",
  "PMT2",
  "PMT3",
  "PMT4",
  "PMT5",
  "PMT6",
  "PMT7",
  "PRENOTE1",
  "PRENOTE2",
  "PRENOTE5",
  "ADDRESS1",
  "ADDRESS2",
  "ADDRESS3",
  "ADDRESS5",
  "ADDRESS6",
  "ADDRESS7",
] as const;

export default scenarios.map((scenario) => {
  paymentScenarios[scenario].claim.leave_dates = [start, end];
  paymentScenarios[scenario].claim.metadata = {
    ...paymentScenarios[scenario].claim.metadata,
    quantity: scenario !== "ADDRESS7" ? 30 : 5,
  };
  return paymentScenarios[scenario];
});
