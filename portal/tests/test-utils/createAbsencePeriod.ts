import { AbsencePeriod } from "src/models/AbsencePeriod";
import { StatusTagMap } from "src/pages/applications/status";
import faker from "faker";

// Cache the previously used date so we incrementally increase it,
// producing more realistic data.
let endDate: Date;

/**
 * Create an absence period for use in testing. Any attributes that are not passed
 * in will have a random, faked value provided.
 */
export const createAbsencePeriod = (partialAttrs: Partial<AbsencePeriod>) => {
  const startDate = faker.date.soon(14, endDate);
  endDate = faker.date.soon(14, startDate);

  const defaultAbsencePeriod = {
    absence_period_start_date: startDate.toISOString().substring(0, 10),
    absence_period_end_date: endDate.toISOString().substring(0, 10),
    fineos_leave_request_id: faker.datatype.uuid(),
    period_type: faker.random.arrayElement<AbsencePeriod["period_type"]>([
      "Continuous",
      "Intermittent",
      "Reduced Schedule",
    ]),
    request_decision: faker.random.arrayElement<keyof typeof StatusTagMap>(
      Object.keys(StatusTagMap) as Array<keyof typeof StatusTagMap>
    ),
  };

  return new AbsencePeriod({ ...defaultAbsencePeriod, ...partialAttrs });
};

export default createAbsencePeriod;
