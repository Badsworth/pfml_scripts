import { MockClaimBuilder } from "../test-utils";

describe("Claim", () => {
  describe("#isCompleted", () => {
    it("returns true when the Claim status is 'completed'", () => {
      const emptyClaim = new MockClaimBuilder().create();
      const completedClaim = new MockClaimBuilder().completed().create();

      expect(emptyClaim.isCompleted).toBe(false);
      expect(completedClaim.isCompleted).toBe(true);
    });
  });

  describe("#isSubmitted", () => {
    it("returns true when the Claim status is 'submitted'", () => {
      const emptyClaim = new MockClaimBuilder().create();
      const submittedClaim = new MockClaimBuilder().submitted().create();

      expect(emptyClaim.isSubmitted).toBe(false);
      expect(submittedClaim.isSubmitted).toBe(true);
    });
  });

  describe("leave type getters", () => {
    const emptyClaim = new MockClaimBuilder().create();
    const claimWithContinuousLeaveData = new MockClaimBuilder()
      .continuous()
      .create();
    const claimWithIntermittentLeaveData = new MockClaimBuilder()
      .intermittent()
      .create();
    const claimWithReducedLeaveData = new MockClaimBuilder()
      .reducedSchedule()
      .create();
    const claimWithMultipleLeaveDurationTypes = new MockClaimBuilder()
      .continuous()
      .intermittent()
      .reducedSchedule()
      .create();

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
        expect(claimWithMultipleLeaveDurationTypes.isReducedSchedule).toBe(
          true
        );
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
});
