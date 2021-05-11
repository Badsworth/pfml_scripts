import { renderWithAppLogic, simulateEvents } from "../../test-utils";
import ConcurrentLeavesIntroIntro from "../../../src/pages/applications/concurrent-leaves-intro";

jest.mock("../../../src/hooks/useAppLogic");

const setup = (claimAttrs = {}) => {
  const { appLogic, claim, wrapper } = renderWithAppLogic(
    ConcurrentLeavesIntroIntro,
    {
      claimAttrs,
    }
  );

  const { submitForm } = simulateEvents(wrapper);

  return {
    appLogic,
    claim,
    submitForm,
    wrapper,
  };
};

describe("ConcurrentLeavesIntroIntro", () => {
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
