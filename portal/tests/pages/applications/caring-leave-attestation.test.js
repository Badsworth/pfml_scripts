import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import CaringLeaveAttestation from "../../../src/pages/applications/caring-leave-attestation";

const setup = () => {
  const { appLogic, claim, wrapper } = renderWithAppLogic(
    CaringLeaveAttestation,
    {
      claimAttrs: new MockBenefitsApplicationBuilder()
        .part1Complete()
        .caringLeaveReason()
        .create(),
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

describe("CaringLeaveAttestation", () => {
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
