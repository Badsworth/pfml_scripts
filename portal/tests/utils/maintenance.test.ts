import {
  isInMaintenanceWindow,
  isMaintenancePageRoute,
  isMaintenanceUpcoming,
  maintenanceTime,
} from "../../src/utils/maintenance";
import dayjs from "dayjs";

describe("maintenance helpers", () => {
  describe("isInMaintenanceWindow", () => {
    it("returns true when start and end times are not provided", () => {
      const value = isInMaintenanceWindow(null, null);

      expect(value).toBe(true);
    });

    it("returns true when current time is within a scheduled maintenance window", () => {
      const startTime = dayjs().subtract(1, "hour").toISOString(); // Started an hour ago
      const endTime = dayjs().add(1, "hour").toISOString(); // Ends in an hour
      const value = isInMaintenanceWindow(startTime, endTime);

      expect(value).toBe(true);
    });

    it("returns true when start is provided but end is omitted", () => {
      const startTime = dayjs().subtract(1, "hour").toISOString(); // Started an hour ago
      const value = isInMaintenanceWindow(startTime, null);

      expect(value).toBe(true);
    });

    it("returns true when end is provided but start is omitted", () => {
      const endTime = dayjs().add(1, "hour").toISOString(); // Ends in an hour
      const value = isInMaintenanceWindow(null, endTime);

      expect(value).toBe(true);
    });

    it("returns false when current time is before a scheduled maintenance window", () => {
      const startTime = dayjs().add(1, "hour").toISOString(); // Starts in an hour
      const endTime = dayjs().add(2, "hour").toISOString(); // Ends in 2 hours
      const value = isInMaintenanceWindow(startTime, endTime);

      expect(value).toBe(false);
    });

    it("returns false when current time is after a scheduled maintenance window", () => {
      const startTime = dayjs().subtract(2, "hour"); // Started 2 hours ago
      const endTime = dayjs().subtract(1, "hour"); // Ended an hour ago
      const value = isInMaintenanceWindow(
        startTime.toISOString(),
        endTime.toISOString()
      );

      expect(value).toBe(false);
    });
  });

  describe("isMaintenanceUpcoming", () => {
    it("returns true if current time is before a scheduled maintenance window", () => {
      const providedStartTime = dayjs().add(1, "hour"); // Maintenance starts in an hour
      const value = isMaintenanceUpcoming(providedStartTime.toISOString(), 1);

      expect(value).toBe(true);
    });

    it("returns false if current time is within or after a scheduled maintenance window", () => {
      const providedStartTime = dayjs().subtract(1, "hour"); // Maintenance started an hour ago
      const value = isMaintenanceUpcoming(providedStartTime.toISOString(), 1);

      expect(value).toBe(false);
    });

    it("returns false if maintenance starts in 25 hours and days = 1", () => {
      const providedStartTime = dayjs().subtract(25, "hour"); // Maintenance starts in 25 hours
      const value = isMaintenanceUpcoming(providedStartTime.toISOString(), 1);

      expect(value).toBe(false);
    });
    it("returns true if maintenance starts in 25 hours and days = 2", () => {
      const providedStartTime = dayjs().subtract(25, "hour"); // Maintenance starts in 25 hours
      const value = isMaintenanceUpcoming(providedStartTime.toISOString(), 2);

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

    it.each([
      ["2021-08-24T03:30:00-04:00", "August 24, 2021 at 3:30 AM"],
      ["2021-11-10T20:59:00-05:00", "November 10, 2021 at 8:59 PM"],
      ["2020-01-01T08:15:30-05:00", "January 1, 2020 at 8:15 AM"],
    ])(
      "returns a formatted date and time when ISO 8601 timestamp %providedDateTime is passed",
      (providedDateTime, expectedDisplayString) => {
        const value = maintenanceTime(providedDateTime);
        expect(value).toBe(expectedDisplayString);
      }
    );
  });
});
