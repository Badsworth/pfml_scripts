import { MockClaimBuilder, renderWithAppLogic } from "../../test-utils";
import { WorkPattern, WorkPatternType } from "../../../src/models/Claim";
import ScheduleRotatingNumberWeeks from "../../../src/pages/claims/schedule-rotating-number-weeks";
import { act } from "react-dom/test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("ScheduleRotatingNumberWeeks", () => {
  let appLogic, wrapper;

  beforeEach(() => {
    const mockClaim = new MockClaimBuilder()
      .continuous()
      .workPattern({
        work_pattern_type: WorkPatternType.rotating,
      })
      .create();

    ({ appLogic, wrapper } = renderWithAppLogic(ScheduleRotatingNumberWeeks, {
      claimAttrs: mockClaim,
    }));
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("creates work pattern days based on number of weeks selected", () => {
    let calledWithParam;

    ["2", "3", "4"].forEach((value) => {
      act(() => {
        wrapper
          .find({ name: "work_pattern.work_pattern_days" })
          .simulate("change", { target: { value } });

        wrapper.find("QuestionPage").simulate("save");
      });

      calledWithParam = appLogic.claims.update.mock.calls[0][1].work_pattern;
      expect(calledWithParam.work_pattern_days.length).toEqual(value * 7);
      expect(calledWithParam.work_pattern_type).toEqual(
        WorkPatternType.rotating
      );

      const workPattern = new WorkPattern({
        work_pattern_days: calledWithParam.work_pattern_days,
      });
      expect(workPattern.weeks.length).toEqual(+value);
      expect(workPattern.minutesWorkedEachWeek.every((min) => min === 0)).toBe(
        true
      );

      appLogic.claims.update.mockClear();
    });
  });

  it("adds 1 week of work_pattern_days and changes type to variable when user selects more than 4 days", () => {
    act(() => {
      wrapper
        .find({ name: "work_pattern.work_pattern_days" })
        .simulate("change", { target: { value: WorkPatternType.variable } });
      wrapper.find("QuestionPage").simulate("save");
    });

    const calledWithParam =
      appLogic.claims.update.mock.calls[0][1].work_pattern;

    expect(calledWithParam.work_pattern_type).toEqual(WorkPatternType.variable);
    expect(calledWithParam.work_pattern_days.length).toEqual(7);
  });

  it("resets hours_worked_per_week", () => {
    act(() => {
      wrapper
        .find({ name: "work_pattern.work_pattern_days" })
        .simulate("change", { target: { value: WorkPatternType.variable } });
      wrapper.find("QuestionPage").simulate("save");
    });

    const calledWithParam = appLogic.claims.update.mock.calls[0][1];
    expect(calledWithParam.hours_worked_per_week).toBeNull();
  });

  it("resets pattern_start_date", () => {
    act(() => {
      wrapper
        .find({ name: "work_pattern.work_pattern_days" })
        .simulate("change", { target: { value: WorkPatternType.variable } });
      wrapper.find("QuestionPage").simulate("save");
    });

    const calledWithParam =
      appLogic.claims.update.mock.calls[0][1].work_pattern;
    expect(calledWithParam.pattern_start_date).toBeNull();
  });
});
