import { MockClaimBuilder, renderWithAppLogic } from "../../test-utils";
import { WorkPattern, WorkPatternType } from "../../../src/models/Claim";
import ScheduleRotating from "../../../src/pages/claims/schedule-rotating";
import { act } from "react-dom/test-utils";
import { round } from "lodash";

jest.mock("../../../src/hooks/useAppLogic");

describe("ScheduleRotating", () => {
  let appLogic, claim, workPattern, wrapper;

  // default to 1 hour on each work pattern day
  const defaultMinutesWorked = 7 * 60;

  beforeEach(() => {
    const work_pattern_days = [1, 2, 3, 4].reduce(
      (wkPattern, i) => WorkPattern.addWeek(wkPattern, defaultMinutesWorked),
      new WorkPattern()
    ).work_pattern_days;

    const mockClaim = new MockClaimBuilder()
      .continuous({ start_date: "2021-01-05" })
      .workPattern({
        work_pattern_type: WorkPatternType.rotating,
        work_pattern_days,
      })
      .create();

    ({ appLogic, claim, wrapper } = renderWithAppLogic(ScheduleRotating, {
      claimAttrs: mockClaim,
    }));

    workPattern = new WorkPattern(claim.work_pattern);
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("fills inputHours with minutes worked each week", () => {
    const inputHoursValues = wrapper
      .find("InputHours")
      .map((el) => el.props().value);
    expect(inputHoursValues).toEqual(workPattern.minutesWorkedEachWeek);
  });

  it("creates pattern_start_date choices relative to leave start date", () => {
    // The previous 4 Sundays from leave start date of 2021-01-05
    const expectedDateChoices = [
      "2021-01-03",
      "2020-12-27",
      "2020-12-20",
      "2020-12-13",
    ];

    const dateChoices = wrapper
      .find({ name: "work_pattern.pattern_start_date" })
      .props()
      .choices.map((choice) => choice.value);

    expect(dateChoices).toEqual(expectedDateChoices);
  });

  it("creates InputHours based on number of weeks in work_pattern", () => {
    expect(wrapper.find("InputHours").length).toEqual(workPattern.weeks.length);
  });

  describe("when inputHours and pattern_start_date change", () => {
    let calledWithParam;
    const minutesWorked = 60 * 70 + 105;

    beforeEach(() => {
      act(() => {
        // change to 70 hours and 105 minutes
        // splits evenly into 615 minutes
        wrapper
          .find("InputHours")
          .first()
          .simulate("change", { target: { value: minutesWorked } });
        wrapper
          .find({ name: "work_pattern.pattern_start_date" })
          .first()
          .simulate("change", {
            target: {
              name: "work_pattern.pattern_start_date",
              value: "2021-01-03",
            },
          });
        wrapper.find("QuestionPage").simulate("save");
      });

      calledWithParam = appLogic.claims.update.mock.calls[0][1];
    });

    it("sends update to API", () => {
      expect(Object.keys(calledWithParam)).toMatchInlineSnapshot(`
        Array [
          "work_pattern",
          "hours_worked_per_week",
        ]
      `);
    });

    it("updates work pattern days when inputHours change for that week", () => {
      const week1 = calledWithParam.work_pattern.work_pattern_days.filter(
        (day) => day.week_number === 1
      );

      expect(week1.every((day) => day.minutes === 615)).toBe(true);
    });

    it("does not update work pattern days for other weeks", () => {
      const weeks = calledWithParam.work_pattern.work_pattern_days.filter(
        (day) => day.week_number !== 1
      );

      expect(weeks.every((day) => day.minutes === 60)).toBe(true);
    });

    it("updates hours_worked_per_week with average of input hours", () => {
      const expectedAverage = (defaultMinutesWorked * 3 + minutesWorked) / 4;
      expect(calledWithParam.hours_worked_per_week).toEqual(
        round(expectedAverage / 60, 2)
      );
    });

    it("updates pattern_start_date", () => {
      expect(calledWithParam.work_pattern.pattern_start_date).toEqual(
        "2021-01-03"
      );
    });
  });
});
