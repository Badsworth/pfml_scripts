import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
} from "../../test-utils";
import CaringLeaveAttestation from "../../../src/pages/applications/caring-leave-attestation";
import { mockRouter } from "next/router";
import routes from "../../../src/routes";

describe("CaringLeaveAttestation", () => {
  it("renders the page", () => {
    mockRouter.pathname = routes.applications.caringLeaveAttestation;
    const { wrapper } = renderWithAppLogic(CaringLeaveAttestation, {
      claimAttrs: new MockBenefitsApplicationBuilder()
        .part1Complete()
        .caringLeaveReason()
        .create(),
    });

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });
});
