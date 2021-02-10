import { MockClaimBuilder, renderWithAppLogic, testHook } from "../test-utils";
import ClaimCollection from "../../src/models/ClaimCollection";
import Dashboard from "../../src/pages/dashboard";
import User from "../../src/models/User";
import { mockRouter } from "next/router";
import routes from "../../src/routes";
import useAppLogic from "../../src/hooks/useAppLogic";

function render(customProps = {}, options = { claims: [] }) {
  let appLogic;
  mockRouter.pathname = routes.applications.dashboard;

  testHook(() => {
    appLogic = useAppLogic();
    appLogic.users.user = new User({ consented_to_data_sharing: true });
    appLogic.claims.claims = new ClaimCollection(options.claims);
    appLogic.claims.hasLoadedAll = true;
  });

  const goToPageForSpy = jest.spyOn(appLogic.portalFlow, "goToPageFor");
  const { wrapper } = renderWithAppLogic(Dashboard, {
    props: { appLogic, ...customProps },
  });

  return { appLogic, goToPageForSpy, wrapper };
}

describe("Dashboard", () => {
  it("renders dashboard content", () => {
    const { wrapper } = render();

    expect(wrapper).toMatchSnapshot();
    wrapper.find("Trans").forEach((trans) => {
      expect(trans.dive()).toMatchSnapshot();
    });
  });

  it("redirects to Dashboard when user has applications and just logged in", () => {
    const claims = [new MockClaimBuilder().create()];

    const { goToPageForSpy } = render(
      {
        query: {
          "logged-in": "true",
        },
      },
      { claims }
    );

    expect(goToPageForSpy).toHaveBeenCalledWith("SHOW_APPLICATIONS");
  });

  it("does not redirect to Dashboard when user has applications but logged-in query isn't set", () => {
    const claims = [new MockClaimBuilder().create()];

    const { goToPageForSpy } = render({}, { claims });

    expect(goToPageForSpy).not.toHaveBeenCalled();
  });
});
