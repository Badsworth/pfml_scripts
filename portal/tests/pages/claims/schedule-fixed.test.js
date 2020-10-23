import { MockClaimBuilder, renderWithAppLogic } from "../../test-utils";
import { WorkPattern, WorkPatternType } from "../../../src/models/Claim";
import { map, sum } from "lodash";

import ScheduleFixed from "../../../src/pages/claims/schedule-fixed";
import { act } from "react-dom/test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("ScheduleFixed", () => {
  let appLogic, workPattern, wrapper;

  // 8 hours days for 7 days
  const defaultMinutesWorked = 8 * 60 * 7;

  beforeEach(() => {
    workPattern = WorkPattern.addWeek(new WorkPattern(), defaultMinutesWorked);
    const mockClaim = new MockClaimBuilder()
      .continuous()
      .workPattern({
        work_pattern_type: WorkPatternType.fixed,
        work_pattern_days: workPattern.work_pattern_days,
      })
      .create();

    ({ appLogic, wrapper } = renderWithAppLogic(ScheduleFixed, {
      claimAttrs: mockClaim,
    }));
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("fills inputHours with minutes worked each day", () => {
    const inputHoursValues = wrapper
      .find("InputHours")
      .map((el) => el.props().value);
    expect(inputHoursValues).toEqual(
      map(workPattern.work_pattern_days, "minutes")
    );
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

    ({ appLogic, wrapper } = renderWithAppLogic(ScheduleFixed, {
      claimAttrs: mockClaim,
      render: "mount",
      diveLevels: 0,
    }));

    wrapper.update();

    const values = wrapper.find("InputHours").map((el) => el.props().value);
    expect(sum(values)).toEqual(0);
  });

  it("updates API with work_pattern_days and hours_worked_per_week", () => {
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

  it("truncates the work_pattern_days to just the first week if work_pattern days have more than 1 week", () => {
    // add a second week
    workPattern = WorkPattern.addWeek(workPattern, 8 * 60 * 5);

    const mockClaim = new MockClaimBuilder()
      .workPattern({
        work_pattern_type: WorkPatternType.fixed,
        work_pattern_days: workPattern.work_pattern_days,
      })
      .create();

    ({ appLogic, wrapper } = renderWithAppLogic(ScheduleFixed, {
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
