import {
  isInMaintenanceWindow,
  isMaintenanceOneDayInFuture,
  isMaintenancePageRoute,
  maintenanceTime,
} from "../../src/utils/maintenance";
import { DateTime } from "luxon";

describe("maintenance helpers", () => {
  describe("isInMaintenanceWindow", () => {
    it("returns true when start and end times are not provided", () => {
      const value = isInMaintenanceWindow(null, null);

      expect(value).toBe(true);
    });

    it("returns true when current time is within a scheduled maintenance window", () => {
      const startTime = DateTime.local().minus({ hours: 1 }); // Started an hour ago
      const endTime = DateTime.local().plus({ hours: 1 }); // Ends in an hour
      const value = isInMaintenanceWindow(startTime, endTime);

      expect(value).toBe(true);
    });

    it("returns true when start is provided but end is omitted", () => {
      const startTime = DateTime.local().minus({ hours: 1 }); // Started an hour ago
      const value = isInMaintenanceWindow(startTime, null);

      expect(value).toBe(true);
    });

    it("returns true when end is provided but start is omitted", () => {
      const endTime = DateTime.local().plus({ hours: 1 }); // Ends in an hour
      const value = isInMaintenanceWindow(null, endTime);

      expect(value).toBe(true);
    });

    it("returns false when current time is before a scheduled maintenance window", () => {
      const startTime = DateTime.local().plus({ hours: 1 }); // Starts in an hour
      const endTime = DateTime.local().plus({ hours: 2 }); // Ends in 2 hours
      const value = isInMaintenanceWindow(startTime, endTime);

      expect(value).toBe(false);
    });

    it("returns false when current time is after a scheduled maintenance window", () => {
      const startTime = DateTime.local().minus({ hours: 2 }); // Started 2 hours ago
      const endTime = DateTime.local().minus({ hours: 1 }); // Ended an hour ago
      const value = isInMaintenanceWindow(startTime, endTime);

      expect(value).toBe(false);
    });
  });

  describe("isMaintenanceOneDayInFuture", () => {
    it("returns false when time is not provided", () => {
      const value = isMaintenanceOneDayInFuture(null);

      expect(value).toBe(false);
    });

    it("returns true if current time is before a scheduled maintenance window", () => {
      const providedStartTime = DateTime.local().plus({ hours: 1 }); // Maintenance starts in an hour
      const value = isMaintenanceOneDayInFuture(providedStartTime);

      expect(value).toBe(true);
    });

    it("returns false if current time is within or after a scheduled maintenance window", () => {
      const providedStartTime = DateTime.local().minus({ hours: 1 }); // Maintenance started an hour ago
      const value = isMaintenanceOneDayInFuture(providedStartTime);

      expect(value).toBe(false);
    });

    it("returns false if current time is more than 24 hours before a scheduled maintenance window", () => {
      const providedStartTime = DateTime.local().minus({ hours: 25 }); // Maintenance starts in 25 hours
      const value = isMaintenanceOneDayInFuture(providedStartTime);

      expect(value).toBe(false);
    });
  });

  describe("isMaintenancePageRoute", () => {
    it("returns true if pathname is in maintenance page routes", () => {
      const value = isMaintenancePageRoute(
        ["/employers", "/applications"],
        "/applications"
      );

      expect(value).toBe(true);
    });

    it("returns true if pathname is in maintenace page route wildcard", () => {
      const value = isMaintenancePageRoute(
        ["/employers", "/applications/*"],
        "/applications/address"
      );

      expect(value).toBe(true);
    });

    it("returns false if pathname is not in maintenance page routes", () => {
      const value = isMaintenancePageRoute(["/employers"], "/applications");

      expect(value).toBe(false);
    });
  });

  describe("maintenanceTime", () => {
    it("returns null if no time is provided", () => {
      const value = maintenanceTime();

      expect(value).toBe(null);
    });

    it("returns a formatted date and time when ISO 8601 timestamp is passed", () => {
      const providedDateTime = "2021-08-24T03:30:00-04:00";
      const value = maintenanceTime(providedDateTime);

      expect(value).toBe(
        DateTime.fromISO(providedDateTime).toLocaleString(
          DateTime.DATETIME_FULL
        )
      );
    });
  });
});
