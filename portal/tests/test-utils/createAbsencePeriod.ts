import { AbsencePeriod } from "src/models/AbsencePeriod";
import { StatusTagMap } from "src/pages/applications/status";
import faker from "faker";

/**
 * Create an absence period for use in testing. Any attributes that are not passed
 * in will have a random, faked value provided.
 */
export const createAbsencePeriod = (partialAttrs: Partial<AbsencePeriod>) => {
  const defaultAbsencePeriod = {
    absence_period_end_date: "2021-09-04",
    absence_period_start_date: "2021-04-09",
    fineos_leave_request_id: faker.datatype.uuid(),
    period_type: faker.random.arrayElement<"Continuous" | "Reduced Schedule">([
      "Continuous",
      "Reduced Schedule",
    ]),
    request_decision: faker.random.arrayElement<keyof typeof StatusTagMap>(
      Object.keys(StatusTagMap) as Array<keyof typeof StatusTagMap>
    ),
  };

  return new AbsencePeriod({ ...defaultAbsencePeriod, ...partialAttrs });
};

export default createAbsencePeriod;
