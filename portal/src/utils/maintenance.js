import { DateTime } from "luxon";

/**
 * @param {string} [start] - ISO 8601 timestamp
 * @param {string} [end] - ISO 8601 timestamp
 * @returns {boolean}
 */
export const isInMaintenanceWindow = (start, end) => {
  // If no time frame is set, the maintenance window is considered
  // always open (when maintenance mode is On)
  if (!start && !end) return true;

  const now = DateTime.local();
  const isAfterStart = start ? now >= DateTime.fromISO(start) : true;
  const isBeforeEnd = end ? now < DateTime.fromISO(end) : true;

  return isAfterStart && isBeforeEnd;
};

/**
 * @param {string} [start] - ISO 8601 timestamp
 * @returns {boolean}
 */
export const isMaintenanceOneDayInFuture = (start) => {
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
 * @param {string[]} maintenancePageRoutes - routes to apply maintenance message to
 * @param {string} pathname - current page's path
 * @returns {boolean}
 */
export const isMaintenancePageRoute = (maintenancePageRoutes, pathname) => {
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
 * @param {string} mTime - ISO 8601 timestamp
 * @returns {string}
 */
export const maintenanceTime = (mTime) => {
  return mTime
    ? DateTime.fromISO(mTime).toLocaleString(DateTime.DATETIME_FULL)
    : null;
};
