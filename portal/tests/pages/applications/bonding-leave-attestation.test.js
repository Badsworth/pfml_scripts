import { renderWithAppLogic, simulateEvents } from "../../test-utils";
import BondingLeaveAttestation from "../../../src/pages/applications/bonding-leave-attestation";

describe("BondingLeaveAttestation", () => {
  it("renders the page", () => {
    const { wrapper } = renderWithAppLogic(BondingLeaveAttestation);

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });

  it("calls goToNextPage when user submits form", async () => {
    const { appLogic, wrapper } = renderWithAppLogic(BondingLeaveAttestation);
    const spy = jest.spyOn(appLogic.portalFlow, "goToNextPage");

    const { submitForm } = simulateEvents(wrapper);
    await submitForm();
    expect(spy).toHaveBeenCalledTimes(1);
  });
});
