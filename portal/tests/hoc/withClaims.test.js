import { mount, shallow } from "enzyme";
import Claim from "../../src/models/Claim";
import ClaimCollection from "../../src/models/ClaimCollection";
import React from "react";
import { act } from "react-dom/test-utils";
import useAppLogic from "../../src/hooks/useAppLogic";
import withClaims from "../../src/hoc/withClaims";

jest.mock("../../src/hooks/useAppLogic");

describe("withClaims", () => {
  let appLogic, wrapper;

  const PageComponent = (props) => <div />;
  const WrappedComponent = withClaims(PageComponent);

  function render() {
    act(() => {
      wrapper = mount(<WrappedComponent appLogic={appLogic} />);
    });
  }

  beforeEach(() => {
    appLogic = useAppLogic();
  });

  it("Shows spinner when claims are not loaded", () => {
    appLogic.claims.claims = null;
    act(() => {
      wrapper = shallow(<WrappedComponent appLogic={appLogic} />);
    });
    expect(wrapper.dive()).toMatchInlineSnapshot(`
      <div
        className="margin-top-8 text-center"
      >
        <Spinner
          aria-valuetext="Loading claims"
        />
      </div>
    `);
  });

  it("loads claims", () => {
    appLogic.claims.claims = null;
    render();
    expect(appLogic.claims.load).toHaveBeenCalledTimes(1);
  });

  it("does not load claims if user has not yet loaded", () => {
    appLogic.user = appLogic.users.user = null;
    render();
    wrapper.update();
    expect(appLogic.claims.load).not.toHaveBeenCalled();
  });

  it("does not load claims if claims have already been loaded", () => {
    appLogic.claims.claims = new ClaimCollection([]);
    render();
    expect(appLogic.claims.load).not.toHaveBeenCalled();
  });

  describe("when claims are loaded", () => {
    beforeEach(() => {
      // Mock initial state of the app
      // these values would be passed from _app.js
      const claim = new Claim({ application_id: "mock-application-id" });
      const claims = new ClaimCollection([claim]);
      appLogic.claims.claims = claims;
      render();
    });

    it("passes through the 'user' prop from the withUser higher order component", () => {
      expect(wrapper.find(PageComponent).prop("user")).toEqual(
        appLogic.users.user
      );
    });

    it("sets the 'claims' prop on the passed component to the loaded claims", () => {
      // Since withClaims is wrapped by withUser, to get the wrapped page component we need to get the child twice
      expect(wrapper.find(PageComponent).prop("claims")).toBeInstanceOf(
        ClaimCollection
      );
      expect(wrapper.find(PageComponent).prop("claims")).toEqual(
        appLogic.claims.claims
      );
    });

    it("renders the wrapped component", () => {
      // Since withClaims is wrapped by withUser, to get the wrapped page component we need to get the child twice
      expect(wrapper.find(PageComponent).name()).toBe("PageComponent");
    });
  });
});
