import { renderWithAppLogic, simulateEvents } from "../../test-utils";
import ConcurrentLeavesDetails from "../../../src/pages/applications/concurrent-leaves-details";

jest.mock("../../../src/hooks/useAppLogic");

const setup = (claimAttrs = { employer_fein: "12-3456789" }) => {
  const {
    appLogic,
    claim,
    wrapper,
  } = renderWithAppLogic(ConcurrentLeavesDetails, { claimAttrs });

  const { changeField, submitForm } = simulateEvents(wrapper);

  return {
    appLogic,
    changeField,
    claim,
    submitForm,
    wrapper,
  };
};

describe("ConcurrentLeavesDetails", () => {
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
