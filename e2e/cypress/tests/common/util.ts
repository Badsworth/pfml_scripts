import {
  ApplicationLeaveDetails,
  ContinuousLeavePeriods,
} from "../../../src/api";

export function lookup<M extends { [k: string]: unknown }, K extends keyof M>(
  key: K,
  map: M
): M[K] {
  if (key in map) {
    return map[key];
  }
  throw new Error(`Unable to find ${key} in lookup map`);
}

export function checkIfContinuous(details: ApplicationLeaveDetails): boolean {
  if (details["continuous_leave_periods"]?.length !== 0) {
    return true;
  } else {
    return false;
  }
}

export function checkIfReduced(details: ApplicationLeaveDetails): boolean {
  if (details["reduced_schedule_leave_periods"]?.length !== 0) {
    return true;
  } else {
    return false;
  }
}

export function checkIfIntermittent(details: ApplicationLeaveDetails): boolean {
  if (details["reduced_schedule_leave_periods"]?.length !== 0) {
    return true;
  } else {
    return false;
  }
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

export function formatDateString(d: Date): string {
  const newDate = new Date(d);
  const month = (newDate.getMonth() + 1).toString();
  const day = newDate.getUTCDate().toString();
  const year = newDate.getUTCFullYear().toString();
  return month.padStart(2, "0") + "/" + day.padStart(2, "0") + "/" + year;
}
