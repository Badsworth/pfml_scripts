import {
  MockClaimBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import WorkPatternType from "../../../src/pages/applications/work-pattern-type";
import { WorkPatternType as WorkPatternTypeEnum } from "../../../src/models/Claim";
import { act } from "react-dom/test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("WorkPatternType", () => {
  it("renders the page with expected content", () => {
    const { wrapper } = renderWithAppLogic(WorkPatternType);

    expect(wrapper).toMatchSnapshot();
  });

  it("resets hours_worked_per_week to null and work_pattern_days to empty array when type changes", () => {
    const { appLogic, wrapper } = renderWithAppLogic(WorkPatternType, {
      claimAttrs: new MockClaimBuilder().fixedWorkPattern().create(),
    });
    const { changeRadioGroup } = simulateEvents(wrapper);

    changeRadioGroup(
      "work_pattern.work_pattern_type",
      WorkPatternTypeEnum.variable
    );

    act(() => {
      wrapper.find("QuestionPage").simulate("save");
    });

    const calledWithParam = appLogic.claims.update.mock.calls[0][1];

    expect(calledWithParam.hours_worked_per_week).toEqual(null);
    expect(calledWithParam.work_pattern.work_pattern_days).toEqual([]);
    expect(calledWithParam.work_pattern.work_pattern_type).toEqual(
      WorkPatternTypeEnum.variable
    );
  });

  it("does not reset hours_worked_per_week to null and work_pattern_days to empty array when type changes", () => {
    const { appLogic, wrapper } = renderWithAppLogic(WorkPatternType, {
      claimAttrs: new MockClaimBuilder().fixedWorkPattern().create(),
    });
    const { changeRadioGroup } = simulateEvents(wrapper);

    changeRadioGroup(
      "work_pattern.work_pattern_type",
      WorkPatternTypeEnum.fixed
    );

    act(() => {
      wrapper.find("QuestionPage").simulate("save");
    });

    const calledWithParam = appLogic.claims.update.mock.calls[0][1];

    expect(calledWithParam.hours_worked_per_week).toBeUndefined();
    expect(calledWithParam.work_pattern.work_pattern_days).toBeUndefined();
    expect(calledWithParam.work_pattern.work_pattern_type).toEqual(
      WorkPatternTypeEnum.fixed
    );
  });
});
