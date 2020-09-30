import { MockClaimBuilder } from "../test-utils";

describe("Claim", () => {
  let emptyClaim;

  beforeEach(() => {
    emptyClaim = new MockClaimBuilder().create();
  });

  describe("#isCompleted", () => {
    it("returns true when the Claim status is 'completed'", () => {
      const completedClaim = new MockClaimBuilder().completed().create();

      expect(emptyClaim.isCompleted).toBe(false);
      expect(completedClaim.isCompleted).toBe(true);
    });
  });

  describe("#isSubmitted", () => {
    it("returns true when the Claim status is 'submitted'", () => {
      const submittedClaim = new MockClaimBuilder().submitted().create();

      expect(emptyClaim.isSubmitted).toBe(false);
      expect(submittedClaim.isSubmitted).toBe(true);
    });
  });

  it("#isBondingLeave returns true when the Claim reason is bonding", () => {
    const claimWithReason = new MockClaimBuilder()
      .bondingBirthLeaveReason()
      .create();

    expect(emptyClaim.isMedicalLeave).toBe(false);
    expect(claimWithReason.isBondingLeave).toBe(true);
  });

  it("#isMedicalLeave returns true when the Claim reason is medical", () => {
    const claimWithReason = new MockClaimBuilder()
      .medicalLeaveReason()
      .create();

    expect(emptyClaim.isMedicalLeave).toBe(false);
    expect(claimWithReason.isMedicalLeave).toBe(true);
  });

  describe("leave period getters", () => {
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

    describe("#fullName", () => {
      it("returns formatted full name", () => {
        const claimWithVerifiedId = new MockClaimBuilder()
          .verifiedId()
          .create();
        expect(claimWithVerifiedId.fullName).toEqual("Jane Doe");
      });

      it("returns formatted name with middle name", () => {
        const claimWithMiddleName = new MockClaimBuilder()
          .verifiedId("John")
          .create();
        expect(claimWithMiddleName.fullName).toEqual("Jane John Doe");
      });
    });
  });
});
