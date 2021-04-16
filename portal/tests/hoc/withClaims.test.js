import Claim from "../../src/models/Claim";
import ClaimCollection from "../../src/models/ClaimCollection";
import React from "react";
import User from "../../src/models/User";
import { act } from "react-dom/test-utils";
import { mount } from "enzyme";
import useAppLogic from "../../src/hooks/useAppLogic";
import withClaims from "../../src/hoc/withClaims";

jest.mock("../../src/hooks/useAppLogic");

describe("withClaims", () => {
  function setup(appLogic, query = {}) {
    let wrapper;

    act(() => {
      const PageComponent = () => <div />;
      const WrappedComponent = withClaims(PageComponent);

      wrapper = mount(<WrappedComponent appLogic={appLogic} query={query} />);
    });

    return { wrapper };
  }

  it("shows spinner when claims aren't loaded yet", () => {
    const appLogic = useAppLogic();
    appLogic.claims.hasLoadedAll = false;

    const { wrapper } = setup(appLogic);

    expect(wrapper.find("Spinner").exists()).toBe(true);
  });

  it("sets user and claims prop on page component when claims are loaded", () => {
    const claimsCollection = new ClaimCollection([
      new Claim({
        fineos_absence_id: "abs-1",
      }),
    ]);
    const appLogic = useAppLogic();
    appLogic.claims.claims = claimsCollection;
    appLogic.claims.hasLoadedAll = true;

    const { wrapper } = setup(appLogic);
    const pageProps = wrapper.find("PageComponent").props();

    expect(pageProps.user).toBeInstanceOf(User);
    expect(pageProps.claims).toBe(claimsCollection);
  });

  it("makes request with 0 as page index if value is not provided", () => {
    const appLogic = useAppLogic();
    appLogic.claims.hasLoadedAll = false;
    const query = { page: null };

    setup(appLogic, query);

    expect(appLogic.claims.loadAll).toHaveBeenCalledWith(0);
  });

  it("makes request with zero-based page index if value is provided", () => {
    const appLogic = useAppLogic();
    appLogic.claims.hasLoadedAll = false;
    const query = { page: "3" };

    setup(appLogic, query);

    expect(appLogic.claims.loadAll).toHaveBeenCalledWith(2);
  });
});
