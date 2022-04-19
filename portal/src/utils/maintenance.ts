import { ISO8601Timestamp } from "../../types/common";
import dayjs from "dayjs";

export const isInMaintenanceWindow = (
  start?: ISO8601Timestamp | null,
  end?: ISO8601Timestamp | null
) => {
  // If no time frame is set, the maintenance window is considered
  // always open (when maintenance mode is On)
  if (!start && !end) return true;

  const now = dayjs();
  const isAfterStart = start ? now >= dayjs(start) : true;
  const isBeforeEnd = end ? now < dayjs(end) : true;

  return isAfterStart && isBeforeEnd;
};

export const isMaintenanceUpcoming = (
  start: ISO8601Timestamp,
  days: number
) => {
  if (!start) return false;

  const now = dayjs();
  const maintenanceStartTime = dayjs(start);
  // We want to avoid showing maintenance-related content too far ahead
  // of the beginning of the window.
  const bannerWindow = dayjs(start).subtract(days, "day");
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
    // includes specific page? (pathname doesn't include a trailing slash):
    maintenancePageRoutes.includes(pathname) ||
    // or pages matching a wildcard? (e.g /applications/* or /* for site-wide):
    maintenancePageRoutes.some(
      (maintenancePageRoute) =>
        maintenancePageRoute.endsWith("*") &&
        pathname.startsWith(maintenancePageRoute.split("*")[0])
    )
  );
};

/**
 * Returns formatted maintenance time
 */
export const maintenanceTime = (mTime?: ISO8601Timestamp | null) => {
  return mTime
    ? new Intl.DateTimeFormat("default", {
        dateStyle: "long",
        timeStyle: "short",
      }).format(dayjs(mTime).toDate())
    : null;
};
