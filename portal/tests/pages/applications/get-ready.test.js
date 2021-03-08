import {
  MockClaimBuilder,
  renderWithAppLogic,
  testHook,
} from "../../test-utils";
import ClaimCollection from "../../../src/models/ClaimCollection";
import GetReady from "../../../src/pages/applications/get-ready";
import User from "../../../src/models/User";
import { mockRouter } from "next/router";
import routes from "../../../src/routes";
import useAppLogic from "../../../src/hooks/useAppLogic";

function render(customProps = {}, options = { claims: [] }) {
  let appLogic;
  mockRouter.pathname = routes.applications.getReady;

  testHook(() => {
    appLogic = useAppLogic();
    appLogic.users.user = new User({ consented_to_data_sharing: true });
    appLogic.claims.claims = new ClaimCollection(options.claims);
    appLogic.claims.hasLoadedAll = true;
  });

  const { wrapper } = renderWithAppLogic(GetReady, {
    props: { appLogic, ...customProps },
  });

  return { appLogic, wrapper };
}

describe("GetReady", () => {
  it("renders get ready content", () => {
    const { wrapper } = render();

    expect(wrapper).toMatchSnapshot();

    wrapper.find("Trans").forEach((trans) => {
      expect(trans.dive()).toMatchSnapshot();
    });
  });

  it("doesn't show link to applications when claims do not exist", () => {
    const { wrapper } = render();

    expect(wrapper.find("Link").exists()).toBe(false);
  });

  it("shows link to applications when claims exist", () => {
    const claims = [new MockClaimBuilder().create()];
    const { wrapper } = render({}, { claims });

    expect(wrapper.find("Link")).toMatchInlineSnapshot(`
      <Link
        href="/applications"
      >
        <a
          className="display-inline-block margin-bottom-5"
        >
          View all applications
        </a>
      </Link>
    `);
  });
});
