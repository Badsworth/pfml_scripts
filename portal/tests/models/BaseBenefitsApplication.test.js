import BaseBenefitsApplication from "../../src/models/BaseBenefitsApplication";
import LeaveReason from "../../src/models/LeaveReason";
import { merge } from "lodash";

class TestClaim extends BaseBenefitsApplication {
  constructor(attrs = {}) {
    super();

    // Defaults:
    this.first_name = "Michael";
    this.middle_name = null;
    this.last_name = "Scott";
    this.leave_details = {
      continuous_leave_periods: [],
      intermittent_leave_periods: [],
      reduced_schedule_leave_periods: [],
      reason: null,
    };

    merge(this, attrs);
  }
}

describe("BaseBenefitsApplication", () => {
  let claim,
    claimWithContinuousLeave,
    claimWithIntermittentLeave,
    claimWithMultipleLeavePeriods,
    claimWithReducedLeave;

  beforeEach(() => {
    claim = new TestClaim();
    claimWithContinuousLeave = new TestClaim({
      leave_details: {
        continuous_leave_periods: [
          { start_date: "2021-03-01", end_date: "2021-09-01" },
        ],
      },
    });
    claimWithIntermittentLeave = new TestClaim({
      leave_details: {
        intermittent_leave_periods: [
          { start_date: "2021-02-01", end_date: "2021-08-01" },
        ],
      },
    });
    claimWithMultipleLeavePeriods = new TestClaim({
      leave_details: {
        continuous_leave_periods: [
          { start_date: "2021-03-01", end_date: "2021-09-01" },
        ],
        reduced_schedule_leave_periods: [
          { start_date: "2021-01-01", end_date: "2021-08-01" },
        ],
      },
    });
    claimWithReducedLeave = new TestClaim({
      leave_details: {
        reduced_schedule_leave_periods: [
          { start_date: "2021-01-01", end_date: "2021-08-01" },
        ],
      },
    });
  });

  describe("#fullName", () => {
    it("returns formatted full name", () => {
      expect(claim.fullName).toEqual("Michael Scott");
    });

    it("returns formatted name with middle name", () => {
      const claimWithMiddleName = new TestClaim({
        first_name: "Michael",
        middle_name: "Gary",
        last_name: "Scott",
      });
      expect(claimWithMiddleName.fullName).toEqual("Michael Gary Scott");
    });
  });

  it("#isBondingLeave returns true when the Claim reason is bonding", () => {
    const bondingLeaveClaim = new TestClaim({
      leave_details: { reason: LeaveReason.bonding },
    });
    const medicalLeaveClaim = new TestClaim({
      leave_details: { reason: LeaveReason.medical },
    });

    expect(medicalLeaveClaim.isBondingLeave).toBe(false);
    expect(bondingLeaveClaim.isBondingLeave).toBe(true);
  });

  describe("#isContinuous", () => {
    it("returns true if continuous leave data is set", () => {
      expect(claimWithContinuousLeave.isContinuous).toBe(true);
      expect(claimWithIntermittentLeave.isContinuous).toBe(false);
      expect(claimWithMultipleLeavePeriods.isContinuous).toBe(true);
      expect(claimWithReducedLeave.isContinuous).toBe(false);
    });
  });

  describe("#continuousLeaveDateRange", () => {
    it("returns the expected date range", () => {
      expect(claimWithContinuousLeave.continuousLeaveDateRange()).toEqual(
        "3/1/2021 to 9/1/2021"
      );
    });
  });

  describe("#isReducedSchedule", () => {
    it("returns true if continuous leave data is set", () => {
      expect(claimWithContinuousLeave.isReducedSchedule).toBe(false);
      expect(claimWithIntermittentLeave.isReducedSchedule).toBe(false);
      expect(claimWithMultipleLeavePeriods.isReducedSchedule).toBe(true);
      expect(claimWithReducedLeave.isReducedSchedule).toBe(true);
    });
  });

  describe("#reducedLeaveDateRange", () => {
    it("returns the expected date range", () => {
      expect(claimWithReducedLeave.reducedLeaveDateRange()).toBe(
        "1/1/2021 to 8/1/2021"
      );
    });
  });

  describe("#isIntermittent", () => {
    it("returns true if continuous leave data is set", () => {
      expect(claimWithContinuousLeave.isIntermittent).toBe(false);
      expect(claimWithIntermittentLeave.isIntermittent).toBe(true);
      expect(claimWithMultipleLeavePeriods.isIntermittent).toBe(false);
      expect(claimWithReducedLeave.isIntermittent).toBe(false);
    });
  });

  describe("#intermittentLeaveDateRange", () => {
    it("returns the expected date range", () => {
      expect(claimWithIntermittentLeave.intermittentLeaveDateRange()).toEqual(
        "2/1/2021 to 8/1/2021"
      );
    });
  });

  describe("#leaveStartDate", () => {
    it("returns earliest start_date", () => {
      expect(claimWithContinuousLeave.leaveStartDate).toEqual("2021-03-01");
      expect(claimWithIntermittentLeave.leaveStartDate).toEqual("2021-02-01");
      expect(claimWithMultipleLeavePeriods.leaveStartDate).toEqual(
        "2021-01-01"
      );
      expect(claimWithReducedLeave.leaveStartDate).toEqual("2021-01-01");
    });
  });

  describe("#leaveEndDate", () => {
    it("returns latest end_date", () => {
      expect(claimWithContinuousLeave.leaveEndDate).toEqual("2021-09-01");
      expect(claimWithIntermittentLeave.leaveEndDate).toEqual("2021-08-01");
      expect(claimWithMultipleLeavePeriods.leaveEndDate).toEqual("2021-09-01");
      expect(claimWithReducedLeave.leaveEndDate).toEqual("2021-08-01");
    });
  });

  describe("#otherLeaveStartDate", () => {
    it("returns program start date if leaveStartDate is null", () => {
      const claimWithoutStartDate = new TestClaim();
      expect(claimWithoutStartDate.otherLeaveStartDate).toContain("2021-01-01");
    });

    it("returns program start date if leaveStartDate is prior to program launch in Jan 2021", () => {
      const claimWithEarlyStart = new TestClaim({
        leave_details: {
          continuous_leave_periods: [
            { start_date: "2020-12-25", end_date: "2021-02-01" },
          ],
        },
      });
      expect(claimWithEarlyStart.otherLeaveStartDate).toContain("2021-01-01");
    });

    it("returns 52 week ago date if leaveStartDate is a sunday", () => {
      const claimWithSundayStart = new TestClaim({
        leave_details: {
          continuous_leave_periods: [
            { start_date: "2022-01-09", end_date: "2022-02-01" }, // Jan 9 is a Sunday
          ],
        },
      });
      expect(claimWithSundayStart.otherLeaveStartDate).toContain("2021-01-10");
    });

    it("returns 52 weeks prior to sunday prior to leaveStartDate if leaveStartDate *not* a Sunday", () => {
      const claimWithSundayStart = new TestClaim({
        leave_details: {
          continuous_leave_periods: [
            { start_date: "2022-01-10", end_date: "2022-02-01" }, // Jan 10 is a Monday
          ],
        },
      });
      expect(claimWithSundayStart.otherLeaveStartDate).toContain("2021-01-10");
    });
  });

  it("gracefully handles invalid date receipt", () => {
    const wonkyClaim = new TestClaim({
      leave_details: {
        continuous_leave_periods: [
          {
            end_date: "2021-05-30",
            start_date: "2nn1",
          },
        ],
      },
    });
    expect(wonkyClaim.otherLeaveStartDate).toContain("2021-01-01");
  });
});
