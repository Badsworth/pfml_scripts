import Claim from "../../src/models/Claim";
import ClaimCollection from "../../src/models/ClaimCollection";
import React from "react";
import { act } from "react-dom/test-utils";
import { mount } from "enzyme";
import useAppLogic from "../../src/hooks/useAppLogic";
import withClaim from "../../src/hoc/withClaim";

jest.mock("../../src/hooks/useAppLogic");

describe("withClaim", () => {
  let appLogic, claim_id, wrapper;

  const PageComponent = () => <div />;
  const WrappedComponent = withClaim(PageComponent);

  function render() {
    act(() => {
      wrapper = mount(
        <WrappedComponent appLogic={appLogic} query={{ claim_id }} />
      );
    });
  }

  beforeEach(() => {
    claim_id = "mock-application-id";
    appLogic = useAppLogic();
  });

  it("Shows spinner when claim is not loaded", () => {
    appLogic.claims.claims = new ClaimCollection();

    render();

    expect(wrapper.find("Spinner").exists()).toBe(true);
    expect(wrapper.find("PageComponent").exists()).toBe(false);
  });

  it("loads the claim", () => {
    appLogic.claims.claims = new ClaimCollection();

    render();

    expect(appLogic.claims.load).toHaveBeenCalledTimes(1);
  });

  it("does not load claim if user has not yet loaded", () => {
    appLogic.user = appLogic.users.user = null;
    render();
    wrapper.update();
    expect(appLogic.claims.load).not.toHaveBeenCalled();
  });

  describe("when claim is loaded", () => {
    let claim;

    beforeEach(() => {
      claim = new Claim({ application_id: claim_id });
      appLogic.claims.claims = new ClaimCollection([claim]);
    });

    it("passes through the 'user' prop from the withUser higher order component", () => {
      render();

      expect(wrapper.find("PageComponent").prop("user")).toEqual(
        appLogic.users.user
      );
    });

    it("sets the 'claim' prop on the passed component", () => {
      render();

      expect(wrapper.find("PageComponent").prop("claim")).toBeInstanceOf(Claim);
      expect(wrapper.find("PageComponent").prop("claim")).toEqual(claim);
    });

    it("renders the wrapped component", () => {
      render();

      expect(wrapper.find("PageComponent").exists()).toBe(true);
      expect(wrapper.find("Spinner").exists()).toBe(false);
    });
  });
});
