import {
  DayOfWeek,
  WorkPattern,
  WorkPatternDay,
  WorkPatternType,
} from "../../../src/models/BenefitsApplication";
import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import ScheduleVariable from "../../../src/pages/applications/schedule-variable";

jest.mock("../../../src/hooks/useAppLogic");

const defaultClaim = new MockBenefitsApplicationBuilder()
  .continuous()
  .workPattern({
    work_pattern_days: [],
    work_pattern_type: WorkPatternType.variable,
  })
  .create();

const setup = (claimAttrs = defaultClaim) => {
  const { appLogic, claim, wrapper } = renderWithAppLogic(ScheduleVariable, {
    claimAttrs,
  });

  const { changeField, submitForm } = simulateEvents(wrapper);

  return {
    appLogic,
    changeField,
    claim,
    submitForm,
    wrapper,
  };
};

describe("ScheduleVariable", () => {
  it("renders the form", () => {
    const { wrapper } = setup();

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });

  it("submits hours_worked_per_week and 7 day work pattern when entering hours for the first time", async () => {
    const { appLogic, claim, changeField, submitForm } = setup();

    changeField("work_pattern.work_pattern_days[0].minutes", 60 * 7); // 1 hour each day
    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        hours_worked_per_week: 7,
        work_pattern: {
          work_pattern_days: Object.values(DayOfWeek).map(
            (day_of_week) => new WorkPatternDay({ day_of_week, minutes: 60 })
          ),
        },
      }
    );
  });

  it("submits updated data when user changes their answer", async () => {
    const initialWorkPattern = WorkPattern.createWithWeek(60 * 7); // 1 hour each day
    const { appLogic, claim, changeField, submitForm } = setup(
      new MockBenefitsApplicationBuilder()
        .continuous()
        .workPattern({
          work_pattern_days: initialWorkPattern.work_pattern_days,
          work_pattern_type: WorkPatternType.variable,
        })
        .create()
    );

    changeField("work_pattern.work_pattern_days[0].minutes", 2 * 60 * 7); // 2 hour each day
    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        hours_worked_per_week: 14,
        work_pattern: {
          work_pattern_days: Object.values(DayOfWeek).map(
            (day_of_week) => new WorkPatternDay({ day_of_week, minutes: 120 })
          ),
        },
      }
    );
  });

  it("submits data when user doesn't change their answers", async () => {
    const initialWorkPattern = WorkPattern.createWithWeek(60 * 7); // 1 hour each day
    const { appLogic, claim, submitForm } = setup(
      new MockBenefitsApplicationBuilder()
        .continuous()
        .workPattern({
          work_pattern_days: initialWorkPattern.work_pattern_days,
          work_pattern_type: WorkPatternType.variable,
        })
        .create()
    );

    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        hours_worked_per_week: 7,
        work_pattern: {
          work_pattern_days: Object.values(DayOfWeek).map(
            (day_of_week) => new WorkPatternDay({ day_of_week, minutes: 60 })
          ),
        },
      }
    );
  });

  it("creates a blank work pattern when user doesn't enter a time amount", async () => {
    const { appLogic, claim, submitForm } = setup();

    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        hours_worked_per_week: null,
        work_pattern: {
          work_pattern_days: [],
        },
      }
    );
  });
});
