import { AbsencePeriod } from "src/models/AbsencePeriod";
import EmployerClaim from "../../src/models/EmployerClaim";
import LeaveReason from "src/models/LeaveReason";
import MockDate from "mockdate";
import { MockEmployerClaimBuilder } from "../test-utils";
import { createMockManagedRequirement } from "../../lib/mock-helpers/createMockManagedRequirement";

describe("EmployerClaim", () => {
  describe("#constructor", () => {
    it("instantiates AbsencePeriod for absence_period entries", () => {
      const claim = new EmployerClaim({
        absence_periods: [
          {
            absence_period_start_date: "2021-03-16",
            absence_period_end_date: "2021-03-30",
            fineos_leave_request_id: "abc123",
            request_decision: "Pending",
            reason: LeaveReason.bonding,
            reason_qualifier_one: "",
            reason_qualifier_two: "",
            period_type: "Reduced Schedule",
          },
        ],
      });

      expect(claim.absence_periods).toHaveLength(1);
      expect(claim.absence_periods[0]).toBeInstanceOf(AbsencePeriod);
    });
  });

  describe("#is_reviewable", () => {
    beforeEach(() => {
      MockDate.set("2021-10-10");
    });

    it("returns true if follow up date is in future", () => {
      const claim = new MockEmployerClaimBuilder()
        .reviewable("2022-10-10")
        .create();

      expect(claim.is_reviewable).toBe(true);
    });

    it("returns false if follow up date is in past", () => {
      const claim = new MockEmployerClaimBuilder()
        .reviewable("2020-10-10")
        .create();

      expect(claim.is_reviewable).toBe(false);
    });

    it("returns true if follow up date is the same day", () => {
      const claim = new MockEmployerClaimBuilder()
        .reviewable("2021-10-10")
        .create();

      expect(claim.is_reviewable).toBe(true);
    });

    it("return false if there is no managed requirement", () => {
      const claim = new MockEmployerClaimBuilder().create();

      expect(claim.is_reviewable).toBe(false);
    });
  });

  describe("lastReviewedAt", () => {
    it("returns the most recent ManagedRequirement responded_at", () => {
      const claim = new EmployerClaim({
        absence_periods: [],
        managed_requirements: [
          createMockManagedRequirement({
            responded_at: "2021-02-30",
          }),
          createMockManagedRequirement({
            responded_at: "2021-01-01",
          }),
          createMockManagedRequirement({
            responded_at: "2021-01-30",
          }),
        ],
      });

      expect(claim.lastReviewedAt).toBe("2021-01-01");
    });

    it("returns undefined when there are no ManagedRequirements", () => {
      const claim = new EmployerClaim({
        absence_periods: [],
        managed_requirements: [],
      });

      expect(claim.lastReviewedAt).toBeUndefined();
    });

    it("returns undefined when there are no ManagedRequirements with a responded_at", () => {
      const claim = new EmployerClaim({
        absence_periods: [],
        managed_requirements: [
          createMockManagedRequirement({
            responded_at: null,
            status: "Suppressed",
          }),
        ],
      });

      expect(claim.lastReviewedAt).toBeUndefined();
    });
  });

  describe("wasPreviouslyReviewed", () => {
    it("returns true if any ManagedRequirement has a status of Complete", () => {
      const claim = new EmployerClaim({
        absence_periods: [],
        managed_requirements: [
          createMockManagedRequirement({
            status: "Open",
          }),
          createMockManagedRequirement({
            status: "Complete",
          }),
        ],
      });

      expect(claim.wasPreviouslyReviewed).toBe(true);
    });

    it("returns false if no ManagedRequirement has a status of Complete", () => {
      const claim = new EmployerClaim({
        absence_periods: [],
        managed_requirements: [
          createMockManagedRequirement({
            status: "Open",
          }),
          createMockManagedRequirement({
            status: "Suppressed",
          }),
        ],
      });

      expect(claim.wasPreviouslyReviewed).toBe(false);
    });

    it("returns false if there are no ManagedRequirements", () => {
      const claim = new EmployerClaim({
        absence_periods: [],
        managed_requirements: [],
      });

      expect(claim.wasPreviouslyReviewed).toBe(false);
    });
  });
});
