import {
  ReducedScheduleLeavePeriod,
  WorkPattern,
} from "../../src/models/Claim";
import { DateTime } from "luxon";
import { MockClaimBuilder } from "../test-utils";
import { map } from "lodash";

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

  describe("#isLeaveStartDateInFuture", () => {
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

    it("returns true when hybrid leave start dates are in the future", () => {
      const claim = new MockClaimBuilder()
        .continuous({ start_date: future })
        .reducedSchedule({ start_date: future })
        .create();

      expect(claim.isLeaveStartDateInFuture).toBe(true);
    });

    it("returns false when one of the hybrid leave start dates is in the past", () => {
      const claim = new MockClaimBuilder()
        .continuous({ start_date: past })
        .reducedSchedule({ start_date: future })
        .create();

      expect(claim.isLeaveStartDateInFuture).toBe(false);
    });

    it("returns true when intermittent leave start dates are in the future", () => {
      const claim = new MockClaimBuilder()
        .intermittent({ start_date: future })
        .create();

      expect(claim.isLeaveStartDateInFuture).toBe(true);
    });

    it("returns false when continuous leave start date is in the past", () => {
      const claim = new MockClaimBuilder()
        .continuous({ start_date: past })
        .create();

      expect(claim.isLeaveStartDateInFuture).toBe(false);
    });

    it("returns false when continuous leave start date is the current day", () => {
      const claim = new MockClaimBuilder()
        .continuous({ start_date: now })
        .create();

      expect(claim.isLeaveStartDateInFuture).toBe(false);
    });

    it("returns false when there are no start dates", () => {
      const claim = new MockClaimBuilder().create();

      expect(claim.isLeaveStartDateInFuture).toBe(false);
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

  describe("WorkPattern", () => {
    it("defaults work_pattern_days to a 7 day week with null minutes", () => {
      const workPattern = new WorkPattern();

      expect(workPattern.work_pattern_days.length).toEqual(7);
      expect(workPattern.work_pattern_days).toMatchSnapshot();
    });

    describe("createWithWeek", () => {
      it("creates a WorkPattern, spreading minutes across 7 work_pattern_days", () => {
        const workPattern = WorkPattern.createWithWeek(8 * 60 * 7);
        expect(workPattern.work_pattern_days.length).toEqual(7);
        expect(
          workPattern.work_pattern_days.every((day) => day.minutes === 8 * 60)
        ).toBe(true);
      });

      it("splits minutes evenly if minutes is a multiple of 7", () => {
        const workPattern = WorkPattern.createWithWeek(77 * 60); // 77 hours
        const workPattern2 = WorkPattern.createWithWeek(77 * 60 + 70); // 77 hours and 70 minutes

        workPattern.work_pattern_days.forEach((day) => {
          expect(day.minutes).toEqual(660);
        });

        workPattern2.work_pattern_days.forEach((day) => {
          expect(day.minutes).toEqual(670);
        });
      });

      it("returns week with 0 minutes when 0 minutes are provided", () => {
        const workPattern = WorkPattern.createWithWeek(0);

        workPattern.work_pattern_days.forEach((day) => {
          expect(day.minutes).toEqual(0);
        });
      });

      it("adds a minute to each day until there is no remainder when minutes are not a multiple of 7", () => {
        const workPattern = WorkPattern.createWithWeek(77 * 60 + 18); // 77 hours and 18 minutes

        expect(map(workPattern.work_pattern_days, "minutes")).toEqual([
          663,
          663,
          663,
          663,
          662,
          662,
          662,
        ]);
      });

      it("passes provided attributes to new WorkPattern", () => {
        const workPattern = WorkPattern.createWithWeek(70, {
          work_pattern_type: "Fixed",
        });

        expect(workPattern.work_pattern_type).toEqual("Fixed");
      });
    });

    describe("minutesWorkedPerWeek", () => {
      it("totals minutes worked across all work pattern days", () => {
        const workPattern = WorkPattern.createWithWeek(70 * 60 + 4); // 70 hours and 4 minutes

        expect(workPattern.minutesWorkedPerWeek).toEqual(70 * 60 + 4);
      });

      it("returns null if work_pattern_days are empty", () => {
        const nullValuesWorkPatternDays = new WorkPattern();
        const emptyWorkPatternDays = new WorkPattern({
          work_pattern_days: [],
        });

        expect(nullValuesWorkPatternDays.minutesWorkedPerWeek).toBeNull();
        expect(emptyWorkPatternDays.minutesWorkedPerWeek).toBeNull();
      });
    });
  });
});

describe("ReducedScheduleLeavePeriod", () => {
  describe("totalMinutesOff", () => {
    it("returns null if no minutes fields are set yet", () => {
      const leavePeriod = new ReducedScheduleLeavePeriod();

      expect(leavePeriod.totalMinutesOff).toBeNull();
    });

    it("returns sum of all minutes fields", () => {
      const leavePeriod = new ReducedScheduleLeavePeriod({
        friday_off_minutes: 1,
        monday_off_minutes: 1,
        saturday_off_minutes: 1,
        sunday_off_minutes: 1,
        thursday_off_minutes: 1,
        tuesday_off_minutes: 1,
        wednesday_off_minutes: 1,
      });

      expect(leavePeriod.totalMinutesOff).toBe(7);
    });
  });
});
