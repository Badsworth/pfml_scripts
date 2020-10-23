import { MockClaimBuilder, renderWithAppLogic } from "../../test-utils";
import { WorkPattern, WorkPatternType } from "../../../src/models/Claim";
import { map, sum } from "lodash";
import ScheduleVariable from "../../../src/pages/claims/schedule-variable";
import { act } from "react-dom/test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("ScheduleVariable", () => {
  let appLogic, workPattern, wrapper;

  // 8 hours days for 7 days
  const defaultMinutesWorked = 8 * 60 * 7;

  beforeEach(() => {
    workPattern = WorkPattern.addWeek(new WorkPattern(), defaultMinutesWorked);
    const claim = new MockClaimBuilder()
      .continuous()
      .workPattern({
        work_pattern_days: workPattern.work_pattern_days,
        work_pattern_type: WorkPatternType.variable,
      })
      .create();

    ({ appLogic, wrapper } = renderWithAppLogic(ScheduleVariable, {
      claimAttrs: claim,
    }));
  });

  it("renders the form", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("creates an empty work pattern if work pattern has no days", () => {
    expect.assertions(1);

    const mockClaim = new MockClaimBuilder()
      .continuous()
      .workPattern({
        work_pattern_type: WorkPatternType.fixed,
        work_pattern_days: [],
      })
      .create();

    ({ appLogic, wrapper } = renderWithAppLogic(ScheduleVariable, {
      claimAttrs: mockClaim,
      render: "mount",
      diveLevels: 0,
    }));

    wrapper.update();

    expect(wrapper.find("InputHours").props().value).toEqual(0);
  });

  it("updates API with work_pattern_days and hours_worked_per_week", () => {
    const changedMinutes = 8 * 60 * 7;
    act(() => {
      wrapper
        .find("InputHours")
        .simulate("change", { target: { value: changedMinutes } });
      wrapper.find("QuestionPage").simulate("save");
    });

    const {
      hours_worked_per_week,
      work_pattern,
    } = appLogic.claims.update.mock.calls[0][1];

    expect(hours_worked_per_week).toEqual(changedMinutes / 60);
    expect(work_pattern.work_pattern_days.length).toEqual(7);
    expect(sum(map(work_pattern.work_pattern_days, "minutes"))).toEqual(
      changedMinutes
    );
  });

  it("truncates the work_pattern_days to just the first week if work_pattern days have more than 1 week", () => {
    // add a second week
    workPattern = WorkPattern.addWeek(workPattern, 8 * 60 * 5);

    const mockClaim = new MockClaimBuilder()
      .workPattern({
        work_pattern_type: WorkPatternType.fixed,
        work_pattern_days: workPattern.work_pattern_days,
      })
      .create();

    ({ appLogic, wrapper } = renderWithAppLogic(ScheduleVariable, {
      claimAttrs: mockClaim,
    }));

    act(() => {
      wrapper.find("QuestionPage").simulate("save");
    });

    const {
      hours_worked_per_week,
      work_pattern,
    } = appLogic.claims.update.mock.calls[0][1];

    expect(hours_worked_per_week).toEqual(defaultMinutesWorked / 60);
    expect(work_pattern.work_pattern_days.length).toEqual(7);
    expect(sum(map(work_pattern.work_pattern_days, "minutes"))).toEqual(
      defaultMinutesWorked
    );
  });
});
