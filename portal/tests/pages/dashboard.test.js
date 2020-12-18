import Dashboard from "../../src/pages/dashboard";
import { mockRouter } from "next/router";
import { renderWithAppLogic } from "../test-utils";
import routes from "../../src/routes";

describe("Dashboard", () => {
  it("renders dashboard content", () => {
    mockRouter.pathname = routes.applications.dashboard;

    const { wrapper } = renderWithAppLogic(Dashboard, {
      diveLevels: 1,
    });

    expect(wrapper).toMatchSnapshot();
    wrapper.find("Trans").forEach((trans) => {
      expect(trans.dive()).toMatchSnapshot();
    });
  });

  it("renders post-launch content when when claimantShowJan1ApplicationInstructions is true", () => {
    process.env.featureFlags = {
      claimantShowJan1ApplicationInstructions: true,
    };
    mockRouter.pathname = routes.applications.dashboard;

    const { wrapper } = renderWithAppLogic(Dashboard, {
      diveLevels: 1,
    });

    wrapper.find("Trans").forEach((trans) => {
      expect(trans.dive()).toMatchSnapshot();
    });
  });
});
