import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import {
  WorkPattern,
  WorkPatternType,
} from "../../../src/models/BenefitsApplication";
import { map, sum } from "lodash";

import ScheduleFixed from "../../../src/pages/applications/schedule-fixed";

jest.mock("../../../src/hooks/useAppLogic");

const MINUTES_WORKED_PER_WEEK = 60 * 8 * 7;

const setup = (claim) => {
  if (!claim) {
    claim = new MockBenefitsApplicationBuilder()
      .continuous()
      .workPattern({
        work_pattern_type: WorkPatternType.fixed,
      })
      .create();
  }

  const { appLogic, wrapper } = renderWithAppLogic(ScheduleFixed, {
    claimAttrs: claim,
  });

  const { changeField, submitForm } = simulateEvents(wrapper);

  return { appLogic, changeField, claim, submitForm, wrapper };
};

describe("ScheduleFixed", () => {
  it("renders the page", () => {
    const { wrapper } = setup();
    expect(wrapper).toMatchSnapshot();
  });

  it("displays work schedule values that were previously entered", () => {
    const workPattern = WorkPattern.createWithWeek(MINUTES_WORKED_PER_WEEK);
    const claim = new MockBenefitsApplicationBuilder()
      .continuous()
      .workPattern({
        work_pattern_type: WorkPatternType.fixed,
        work_pattern_days: workPattern.work_pattern_days,
      })
      .create();

    const { wrapper } = setup(claim);
    const inputHoursValues = wrapper
      .find("InputHours")
      .map((el) => el.props().value);
    expect(inputHoursValues).toEqual(
      map(workPattern.work_pattern_days, "minutes")
    );
  });

  it("updates the claim's work_pattern_days and hours_worked_per_week when the page is submitted", async () => {
    const { appLogic, changeField, submitForm } = setup();

    for (let day = 0; day < 7; day++) {
      changeField(`work_pattern.work_pattern_days[${day}].minutes`, 8 * 60);
    }
    await submitForm();

    const { hours_worked_per_week, work_pattern } =
      appLogic.benefitsApplications.update.mock.calls[0][1];

    expect(hours_worked_per_week).toEqual(MINUTES_WORKED_PER_WEEK / 60);
    expect(work_pattern.work_pattern_days.length).toEqual(7);
    expect(sum(map(work_pattern.work_pattern_days, "minutes"))).toEqual(
      MINUTES_WORKED_PER_WEEK
    );
  });
});
