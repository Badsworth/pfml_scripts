import {
  AbsencePeriod,
  AbsencePeriodRequestDecision,
} from "src/models/AbsencePeriod";
import LeaveReason from "../../src/models/LeaveReason";
import { faker } from "@faker-js/faker";

// Cache the previously used date so we incrementally increase it,
// producing more realistic data.
let endDate: Date;

/**
 * Create an absence period for use in testing. Any attributes that are not passed
 * in will have a random, faked value provided.
 */
export const createAbsencePeriod = (
  partialAttrs: Partial<AbsencePeriod> = {}
) => {
  const startDate = faker.date.soon(14, endDate?.toISOString());
  endDate = faker.date.soon(14, startDate.toISOString());

  const defaultAbsencePeriod = {
    absence_period_start_date: startDate.toISOString().substring(0, 10),
    absence_period_end_date: endDate.toISOString().substring(0, 10),
    fineos_leave_request_id: faker.datatype.uuid(),
    period_type: faker.random.arrayElement<AbsencePeriod["period_type"]>([
      "Continuous",
      "Intermittent",
      "Reduced Schedule",
    ]),
    reason: faker.random.arrayElement(Object.values(LeaveReason)),
    request_decision: faker.random.arrayElement(
      Object.values(AbsencePeriodRequestDecision)
    ),
  };

  return new AbsencePeriod({ ...defaultAbsencePeriod, ...partialAttrs });
};

export default createAbsencePeriod;
