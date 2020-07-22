import Claim, {
  ContinuousLeavePeriod,
  IntermittentLeavePeriod,
  ReducedScheduleLeavePeriod,
} from "../../src/models/Claim";

describe("Claim", () => {
  const emptyClaim = new Claim();
  const claimWithContinuousLeaveData = new Claim({
    temp: {
      leave_details: {
        continuous_leave_periods: [new ContinuousLeavePeriod()],
      },
    },
  });
  const claimWithReducedLeaveData = new Claim({
    temp: {
      leave_details: {
        reduced_schedule_leave_periods: [new ReducedScheduleLeavePeriod()],
      },
    },
  });
  const claimWithIntermittentLeaveData = new Claim({
    leave_details: {
      intermittent_leave_periods: [new IntermittentLeavePeriod()],
    },
  });
  const claimWithMultipleLeaveDurationTypes = new Claim({
    leave_details: {
      intermittent_leave_periods: [new IntermittentLeavePeriod()],
    },
    temp: {
      leave_details: {
        reduced_schedule_leave_periods: [new ReducedScheduleLeavePeriod()],
        continuous_leave_periods: [new ContinuousLeavePeriod()],
      },
    },
  });

  describe("#isContinuous", () => {
    it("returns true if and only if continuous leave data is set", () => {
      expect(emptyClaim.isContinuous).toBe(false);
      expect(claimWithContinuousLeaveData.isContinuous).toBe(true);
      expect(claimWithReducedLeaveData.isContinuous).toBe(false);
      expect(claimWithIntermittentLeaveData.isContinuous).toBe(false);
      expect(claimWithMultipleLeaveDurationTypes.isContinuous).toBe(true);
    });
  });

  describe("#isReducedSchedule", () => {
    it("returns true if and only if continuous leave data is set", () => {
      expect(emptyClaim.isReducedSchedule).toBe(false);
      expect(claimWithContinuousLeaveData.isReducedSchedule).toBe(false);
      expect(claimWithReducedLeaveData.isReducedSchedule).toBe(true);
      expect(claimWithIntermittentLeaveData.isReducedSchedule).toBe(false);
      expect(claimWithMultipleLeaveDurationTypes.isReducedSchedule).toBe(true);
    });
  });

  describe("#isIntermittent", () => {
    it("returns true if and only if continuous leave data is set", () => {
      expect(emptyClaim.isIntermittent).toBe(false);
      expect(claimWithContinuousLeaveData.isIntermittent).toBe(false);
      expect(claimWithReducedLeaveData.isIntermittent).toBe(false);
      expect(claimWithIntermittentLeaveData.isIntermittent).toBe(true);
      expect(claimWithMultipleLeaveDurationTypes.isIntermittent).toBe(true);
    });
  });
});
