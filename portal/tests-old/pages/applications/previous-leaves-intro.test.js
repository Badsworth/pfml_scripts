import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";

import PreviousLeavesIntro from "../../../src/pages/applications/previous-leaves-intro";

jest.mock("../../../src/hooks/useAppLogic");

const setup = (claimAttrs = {}) => {
  const { appLogic, claim, wrapper } = renderWithAppLogic(PreviousLeavesIntro, {
    claimAttrs,
  });

  const { submitForm } = simulateEvents(wrapper);

  return {
    appLogic,
    claim,
    submitForm,
    wrapper,
  };
};

describe("PreviousLeavesIntro", () => {
  it("renders the page", () => {
    const { wrapper } = setup(
      new MockBenefitsApplicationBuilder().continuous().create()
    );

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
