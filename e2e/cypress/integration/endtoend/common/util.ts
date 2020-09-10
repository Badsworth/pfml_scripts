import {
  ApplicationLeaveDetails,
  ContinuousLeavePeriods,
} from "../../../../src/api";

export function lookup<M extends { [k: string]: unknown }, K extends keyof M>(
  key: K,
  map: M
): M[K] {
  if (key in map) {
    return map[key];
  }
  throw new Error(`Unable to find ${key} in lookup map`);
}

export function getLeaveType(
  details: ApplicationLeaveDetails
): "continuous" | "reduced" | "intermittent" {
  if (details["continuous_leave_periods"]?.length !== 0) {
    return "continuous";
  }
  throw new Error("Wrong Claim");

  /* @Todo 
    Need to account for other leave types ...
  */
}

export function getWeeks(details: ApplicationLeaveDetails): number {
  const numOfWeeks = details.continuous_leave_periods?.reduce(
    (total: number, leave: ContinuousLeavePeriods) => {
      const startDateNum = new Date(leave.start_date as string).getTime();
      const endDateNum = new Date(leave.end_date as string).getTime();
      const dif = Math.floor(
        (endDateNum - startDateNum) / 1000 / 60 / 60 / 24 / 7
      );

      return total + dif;
    },
    0
  );

  return numOfWeeks as number;
}
