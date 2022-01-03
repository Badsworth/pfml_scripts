import { AbsencePeriod } from "src/models/AbsencePeriod";
import EmployerClaim from "../../src/models/EmployerClaim";
import LeaveReason from "src/models/LeaveReason";
import MockDate from "mockdate";
import { MockEmployerClaimBuilder } from "../test-utils";

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
});
