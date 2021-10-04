import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import WorkPatternType from "../../../src/pages/applications/work-pattern-type";
import { WorkPatternType as WorkPatternTypeEnum } from "../../../src/models/BenefitsApplication";

jest.mock("../../../src/hooks/useAppLogic");

const setup = (claimAttrs = {}) => {
  const { appLogic, claim, wrapper } = renderWithAppLogic(WorkPatternType, {
    claimAttrs,
  });

  const { changeRadioGroup, submitForm } = simulateEvents(wrapper);

  return {
    appLogic,
    changeRadioGroup,
    claim,
    submitForm,
    wrapper,
  };
};

describe("WorkPatternType", () => {
  it("renders the page with expected content", () => {
    const { wrapper } = setup();

    expect(wrapper).toMatchSnapshot();
  });

  it("resets hours_worked_per_week to null and work_pattern_days to empty array when type changes", async () => {
    const { appLogic, claim, changeRadioGroup, submitForm } = setup(
      new MockBenefitsApplicationBuilder().fixedWorkPattern().create()
    );

    changeRadioGroup(
      "work_pattern.work_pattern_type",
      WorkPatternTypeEnum.variable
    );
    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        hours_worked_per_week: null,
        work_pattern: {
          work_pattern_days: [],
          work_pattern_type: WorkPatternTypeEnum.variable,
        },
      }
    );
  });

  it("does not reset hours_worked_per_week to null and work_pattern_days to empty array when type does NOT change", async () => {
    const { appLogic, claim, submitForm } = setup(
      new MockBenefitsApplicationBuilder().fixedWorkPattern().create()
    );

    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        work_pattern: {
          work_pattern_type: WorkPatternTypeEnum.fixed,
        },
      }
    );
  });
});
