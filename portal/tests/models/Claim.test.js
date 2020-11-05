import { DayOfWeek, WorkPattern, WorkPatternDay } from "../../src/models/Claim";
import { map, sumBy } from "lodash";
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

  describe("#isChildDateInFuture", () => {
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

      expect(claim.isChildDateInFuture).toBe(true);
    });

    it("returns false for past birth bonding leave", () => {
      const claim = new MockClaimBuilder()
        .bondingBirthLeaveReason(past)
        .create();

      expect(claim.isChildDateInFuture).toBe(false);
    });

    it("returns true for future placement bonding leave", () => {
      const claim = new MockClaimBuilder()
        .bondingFosterCareLeaveReason(future)
        .create();

      expect(claim.isChildDateInFuture).toBe(true);
    });

    it("returns false for past placement bonding leave", () => {
      const claim = new MockClaimBuilder()
        .bondingFosterCareLeaveReason(past)
        .create();

      expect(claim.isChildDateInFuture).toBe(false);
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

      describe("when minutesWorkedPerWeek is provided", () => {
        it("splits minutes evenly if minutes is a multiple of 7", () => {
          const workPattern = WorkPattern.addWeek(new WorkPattern(), 77 * 60); // 77 hours
          const workPattern2 = WorkPattern.addWeek(
            new WorkPattern(),
            77 * 60 + 70 // 77 hours and 70 minutes
          );

          workPattern.work_pattern_days.forEach((day) => {
            expect(day.minutes).toEqual(660);
          });

          workPattern2.work_pattern_days.forEach((day) => {
            expect(day.minutes).toEqual(670);
          });
        });

        it("returns week with 0 minutes when no hours are provided", () => {
          const workPattern = WorkPattern.addWeek(new WorkPattern(), 0);
          const workPattern2 = WorkPattern.addWeek(new WorkPattern());

          workPattern.work_pattern_days.forEach((day) => {
            expect(day.minutes).toEqual(0);
          });

          workPattern2.work_pattern_days.forEach((day) => {
            expect(day.minutes).toEqual(0);
          });
        });

        it("adds a minute to each day until there is no remainder when minutes are not a multiple of 7", () => {
          const workPattern = WorkPattern.addWeek(
            new WorkPattern(),
            77 * 60 + 18 // 77 hours and 18 minutes
          );

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
      });
    });

    describe("updateWeek", () => {
      let workPattern;

      beforeEach(() => {
        workPattern = new WorkPattern({
          work_pattern_days: [createWeek(1), createWeek(2)].flat(),
        });
      });

      it("updates week's minutes", () => {
        workPattern = WorkPattern.updateWeek(workPattern, 2, 77 * 60 + 18);
        expect(sumBy(workPattern.weeks[0], "minutes")).toEqual(0);
        expect(map(workPattern.weeks[1], "minutes")).toEqual([
          663,
          663,
          663,
          663,
          662,
          662,
          662,
        ]);
      });

      it("throws error if weekNumber is out of bounds", () => {
        expect(() =>
          WorkPattern.updateWeek(workPattern, 3, 77 * 60 + 18)
        ).toThrow();
      });
    });

    describe("removeWeek", () => {
      it("removes days from work_pattern_days with given week_number", () => {
        let workPattern = new WorkPattern({
          work_pattern_days: [1, 2, 3, 4].flatMap((week_number) =>
            createWeek(week_number).map((day) => ({
              ...day,
              minutes: week_number * 10 * 60,
            }))
          ),
        });

        workPattern = WorkPattern.removeWeek(workPattern, 3);

        expect(workPattern.work_pattern_days.length).toEqual(21);
        expect(workPattern.weeks.length).toEqual(3);
        // removes week_number 3
        expect(
          workPattern.work_pattern_days.every(
            (day) => day.minutes !== 3 * 10 * 60
          )
        ).toBe(true);
        // what was week_number 4 is now week_number 3
        expect(
          workPattern.weeks[2].every((day) => day.minutes === 4 * 10 * 60)
        ).toBe(true);

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

    describe("minutesWorkedEachWeek", () => {
      it("totals minutes worked each week", () => {
        let workPattern = WorkPattern.addWeek(new WorkPattern(), 70 * 60); // 70 hours
        workPattern = WorkPattern.addWeek(workPattern, 70 * 60 + 4); // 70 hours and 4 minutes

        const minutesWorkedEachWeek = workPattern.minutesWorkedEachWeek;
        expect(minutesWorkedEachWeek[0]).toEqual(70 * 60);
        expect(minutesWorkedEachWeek[1]).toEqual(70 * 60 + 4);
      });
    });
  });
});
