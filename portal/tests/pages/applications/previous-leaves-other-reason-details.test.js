import { renderWithAppLogic, simulateEvents } from "../../test-utils";
import PreviousLeavesOtherReasonDetails from "../../../src/pages/applications/previous-leaves-other-reason-details";

jest.mock("../../../src/hooks/useAppLogic");

const setup = (claimAttrs = {}) => {
  const {
    appLogic,
    claim,
    wrapper,
  } = renderWithAppLogic(PreviousLeavesOtherReasonDetails, { claimAttrs });

  const { changeField, submitForm } = simulateEvents(wrapper);

  return {
    appLogic,
    changeField,
    claim,
    submitForm,
    wrapper,
  };
};

describe("PreviousLeavesOtherReasonDetails", () => {
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
