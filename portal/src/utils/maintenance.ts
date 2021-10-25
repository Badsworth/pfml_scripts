import { DateTime } from "luxon";
import { ISO8601Timestamp } from "../../types/common";

export const isInMaintenanceWindow = (
  start?: ISO8601Timestamp | null,
  end?: ISO8601Timestamp | null
) => {
  // If no time frame is set, the maintenance window is considered
  // always open (when maintenance mode is On)
  if (!start && !end) return true;

  const now = DateTime.local();
  const isAfterStart = start ? now >= DateTime.fromISO(start) : true;
  const isBeforeEnd = end ? now < DateTime.fromISO(end) : true;

  return isAfterStart && isBeforeEnd;
};

export const isMaintenanceOneDayInFuture = (
  start?: ISO8601Timestamp | null
) => {
  if (!start) return false;

  const now = DateTime.local();
  const maintenanceStartTime = DateTime.fromISO(start);
  // We want to avoid showing maintenance-related content too far ahead
  // of the beginning of the window, so we check if it's within a day.
  const bannerWindow = DateTime.fromISO(start).minus({ days: 1 });
  const isBeforeStart = start
    ? now < maintenanceStartTime && now >= bannerWindow
    : true;

  return isBeforeStart;
};

/**
 * Check if a page route should include the maintenance message
 */
export const isMaintenancePageRoute = (
  maintenancePageRoutes: string[],
  pathname: string
) => {
  return (
    maintenancePageRoutes &&
    // includes specific page? (pathname doesn't include a trailing slash):
    (maintenancePageRoutes.includes(pathname) ||
      // or pages matching a wildcard? (e.g /applications/* or /* for site-wide):
      maintenancePageRoutes.some(
        (maintenancePageRoute) =>
          maintenancePageRoute.endsWith("*") &&
          pathname.startsWith(maintenancePageRoute.split("*")[0])
      ))
  );
};

/**
 * Returns formatted maintenance time
 */
export const maintenanceTime = (mTime?: ISO8601Timestamp | null) => {
  return mTime
    ? DateTime.fromISO(mTime).toLocaleString(DateTime.DATETIME_FULL)
    : null;
};
