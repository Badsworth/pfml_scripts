import BondingLeaveAttestation from "../../../src/pages/applications/bonding-leave-attestation";
import { mockRouter } from "next/router";
import { renderWithAppLogic } from "../../test-utils";
import routes from "../../../src/routes";

describe("BondingLeaveAttestation", () => {
  it("renders the page", () => {
    mockRouter.pathname = routes.applications.bondingLeaveAttestation;
    const { wrapper } = renderWithAppLogic(BondingLeaveAttestation);

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });
});
