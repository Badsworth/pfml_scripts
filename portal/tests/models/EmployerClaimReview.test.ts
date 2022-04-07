import { MockEmployerClaimBuilder, createAbsencePeriod } from "../test-utils";
import { AbsencePeriod } from "src/models/AbsencePeriod";
import EmployerClaimReview from "../../src/models/EmployerClaimReview";
import MockDate from "mockdate";
import { createMockManagedRequirement } from "../../lib/mock-helpers/createMockManagedRequirement";

describe("EmployerClaim", () => {
  const claimWithMultiAbsencePeriods = new EmployerClaimReview({
    absence_periods: [
      createAbsencePeriod({
        absence_period_start_date: "2021-03-13",
        absence_period_end_date: "2021-03-16",
      }),
      createAbsencePeriod({
        absence_period_start_date: "2021-03-17",
        absence_period_end_date: "2021-03-30",
      }),
    ],
  });

  describe("#constructor", () => {
    it("instantiates AbsencePeriod for absence_period entries", () => {
      const claim = new EmployerClaimReview({
        absence_periods: [createAbsencePeriod()],
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
      const claim = new EmployerClaimReview({
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
      const claim = new EmployerClaimReview({
        absence_periods: [],
        managed_requirements: [],
      });

      expect(claim.lastReviewedAt).toBeUndefined();
    });

    it("returns undefined when there are no ManagedRequirements with a responded_at", () => {
      const claim = new EmployerClaimReview({
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
      const claim = new EmployerClaimReview({
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
      const claim = new EmployerClaimReview({
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
      const claim = new EmployerClaimReview({
        absence_periods: [],
        managed_requirements: [],
      });

      expect(claim.wasPreviouslyReviewed).toBe(false);
    });
  });

  describe("#leaveStartDate", () => {
    it("returns earliest absence period start date", () => {
      expect(claimWithMultiAbsencePeriods.leaveStartDate).toBe("2021-03-13");
    });

    it("returns null if no absence period", () => {
      const claim = new EmployerClaimReview({
        absence_periods: [],
      });

      expect(claim.leaveStartDate).toBeNull();
    });
  });

  describe("#leaveEndDate", () => {
    it("returns latest absence period end date", () => {
      expect(claimWithMultiAbsencePeriods.leaveEndDate).toBe("2021-03-30");
    });

    it("returns null if no absence period", () => {
      const claim = new EmployerClaimReview({
        absence_periods: [],
      });

      expect(claim.leaveEndDate).toBeNull();
    });
  });

  describe("#fullName", () => {
    it("returns formatted full name", () => {
      const claim = new EmployerClaimReview({
        absence_periods: [],
        first_name: "Michael",
        middle_name: "",
        last_name: "Scott",
      });
      expect(claim.fullName).toEqual("Michael Scott");
    });

    it("returns formatted name with middle name", () => {
      const claim = new EmployerClaimReview({
        absence_periods: [],
        first_name: "Michael",
        middle_name: "Gary",
        last_name: "Scott",
      });
      expect(claim.fullName).toEqual("Michael Gary Scott");
    });
  });

  describe("#isIntermittent", () => {
    it("returns false when there is no intermittent absence period", () => {
      const claim = new EmployerClaimReview({
        absence_periods: [
          createAbsencePeriod({
            period_type: "Continuous",
          }),
          createAbsencePeriod({
            period_type: "Reduced Schedule",
          }),
        ],
      });
      expect(claim.isIntermittent).toBe(false);
    });

    it("returns true when there is one intermittent absence period", () => {
      const claim = new EmployerClaimReview({
        absence_periods: [
          createAbsencePeriod({
            period_type: "Continuous",
          }),
          createAbsencePeriod({
            period_type: "Reduced Schedule",
          }),
          createAbsencePeriod({
            period_type: "Intermittent",
          }),
        ],
      });
      expect(claim.isIntermittent).toBe(true);
    });
  });

  describe("#isCaringLeave", () => {
    it("returns false when there is no caring leave absence period", () => {
      const claim = new EmployerClaimReview({
        absence_periods: [
          createAbsencePeriod({
            reason: "Child Bonding",
          }),
          createAbsencePeriod({
            reason: "Pregnancy/Maternity",
          }),
        ],
      });
      expect(claim.isCaringLeave).toBe(false);
    });

    it("returns true when there is one caring leave absence period", () => {
      const claim = new EmployerClaimReview({
        absence_periods: [
          createAbsencePeriod({
            reason: "Child Bonding",
          }),
          createAbsencePeriod({
            reason: "Care for a Family Member",
          }),
        ],
      });
      expect(claim.isCaringLeave).toBe(true);
    });
  });
});
