import { DayOfWeek, WorkPattern, WorkPatternDay } from "../../src/models/Claim";
import { DateTime } from "luxon";
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

  describe("#isFutureChildDate", () => {
    const past = "2020-09-30";
    const now = "2020-10-01";
    const future = "2020-10-02";
    let spy;

    beforeAll(() => {
      spy = jest.spyOn(DateTime, "local").mockImplementation(() => {
        return {
          toISODate: () => now,
        };
      });
    });

    afterAll(() => {
      spy.mockRestore();
    });

    it("returns true for future birth bonding leave", () => {
      const claim = new MockClaimBuilder()
        .bondingBirthLeaveReason(future)
        .create();

      expect(claim.isFutureChildDate).toBe(true);
    });

    it("returns false for past birth bonding leave", () => {
      const claim = new MockClaimBuilder()
        .bondingBirthLeaveReason(past)
        .create();

      expect(claim.isFutureChildDate).toBe(false);
    });

    it("returns true for future placement bonding leave", () => {
      const claim = new MockClaimBuilder()
        .bondingFosterCareLeaveReason(future)
        .create();

      expect(claim.isFutureChildDate).toBe(true);
    });

    it("returns false for past placement bonding leave", () => {
      const claim = new MockClaimBuilder()
        .bondingFosterCareLeaveReason(past)
        .create();

      expect(claim.isFutureChildDate).toBe(false);
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

  describe("WorkPattern", () => {
    const createWeek = (week_number) => {
      return Object.values(DayOfWeek).map(
        (day_of_week) => new WorkPatternDay({ day_of_week, week_number })
      );
    };

    describe("weeks", () => {
      it("groups work_pattern_days by week_number", () => {
        const workPattern = new WorkPattern({
          work_pattern_days: [1, 2, 3, 4].flatMap((week_number) =>
            createWeek(week_number)
          ),
        });

        const weeks = workPattern.weeks;

        expect(weeks.length).toEqual(4);

        weeks.forEach((week, i) => {
          expect(week.length).toEqual(7);
          expect(week.map((day) => day.day_of_week)).toEqual(
            Object.values(DayOfWeek)
          );
          expect(week.every((day) => day.week_number === i + 1)).toBe(true);
        });
      });
    });

    describe("addWeek", () => {
      it("adds 7 days to work_pattern_days", () => {
        let workPattern = new WorkPattern({
          work_pattern_days: createWeek(1),
        });

        workPattern = WorkPattern.addWeek(workPattern);
        expect(workPattern.work_pattern_days.length).toEqual(14);
        expect(workPattern.weeks.length).toEqual(2);

        workPattern.weeks.forEach((week, i) => {
          expect(week.length).toEqual(7);
          expect(week.map((day) => day.day_of_week)).toEqual(
            Object.values(DayOfWeek)
          );
          expect(week.every((day) => day.week_number === i + 1)).toBe(true);
        });
      });

      it("adds 7 days to work_pattern days when days are empty", () => {
        let workPattern = new WorkPattern();

        workPattern = WorkPattern.addWeek(workPattern);
        expect(workPattern.work_pattern_days.length).toEqual(7);
      });
    });

    describe("removeWeek", () => {
      it("removes days from work_pattern_days with given week_number", () => {
        let workPattern = new WorkPattern({
          work_pattern_days: [1, 2, 3, 4].flatMap((week_number) =>
            createWeek(week_number).map((day) => ({
              ...day,
              hours: week_number * 10,
            }))
          ),
        });

        workPattern = WorkPattern.removeWeek(workPattern, 3);

        expect(workPattern.work_pattern_days.length).toEqual(21);
        expect(workPattern.weeks.length).toEqual(3);
        expect(
          workPattern.work_pattern_days.every((day) => day.hours !== 30)
        ).toBe(true);
        expect(workPattern.weeks[2].every((day) => day.hours === 40)).toBe(
          true
        );

        workPattern.weeks.forEach((week, i) => {
          expect(week.length).toEqual(7);
          expect(week.map((day) => day.day_of_week)).toEqual(
            Object.values(DayOfWeek)
          );
          expect(week.every((day) => day.week_number === i + 1)).toBe(true);
        });
      });

      it("it fails silently when work_pattern_days is empty or attempts to remove an week_number that doesn't exist", () => {
        let workPattern = new WorkPattern();
        workPattern = WorkPattern.removeWeek(workPattern, 3);

        expect(workPattern.work_pattern_days).toEqual([]);
      });
    });
  });
});
