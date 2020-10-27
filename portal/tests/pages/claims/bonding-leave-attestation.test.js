import BondingLeaveAttestation from "../../../src/pages/claims/bonding-leave-attestation";
import { renderWithAppLogic } from "../../test-utils";

describe("BondingLeaveAttestation", () => {
  it("renders the page", () => {
    const { wrapper } = renderWithAppLogic(BondingLeaveAttestation);

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });

  it("calls goToNextPage when user clicks button", () => {
    const { appLogic, wrapper } = renderWithAppLogic(BondingLeaveAttestation);
    const spy = jest.spyOn(appLogic.portalFlow, "goToNextPage");

    wrapper.find("Button").simulate("click");
    expect(spy).toHaveBeenCalledTimes(1);
  });
});
