import { renderWithAppLogic, simulateEvents } from "../../test-utils";
import PreviousLeavesOtherReason from "../../../src/pages/applications/previous-leaves-other-reason";

jest.mock("../../../src/hooks/useAppLogic");

const setup = (claimAttrs = {}) => {
  const {
    appLogic,
    claim,
    wrapper,
  } = renderWithAppLogic(PreviousLeavesOtherReason, { claimAttrs });

  const { changeField, submitForm } = simulateEvents(wrapper);

  return {
    appLogic,
    changeField,
    claim,
    submitForm,
    wrapper,
  };
};

describe("PreviousLeavesOtherReason", () => {
  it("renders the page", () => {
    const { wrapper } = setup();

    expect(wrapper).toMatchSnapshot();
  });

  it("calls goToNextPage when user submits form", async () => {
    const { appLogic, wrapper } = setup();
    const spy = jest.spyOn(appLogic.portalFlow, "goToNextPage");

    const { submitForm } = simulateEvents(wrapper);
    await submitForm();
    expect(spy).toHaveBeenCalledTimes(1);
  });
});
