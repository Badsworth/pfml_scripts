import { mount, shallow } from "enzyme";
import Claim from "../../src/models/Claim";
import React from "react";
import useAppLogic from "../../src/hooks/useAppLogic";
import withClaim from "../../src/hoc/withClaim";

jest.mock("../../src/hooks/useAppLogic");

describe("WithClaim", () => {
  it("Shows spinner when claims are not loaded", () => {
    const appLogic = useAppLogic();
    appLogic.claims = null;

    const PageComponent = (props) => <div />;

    const WrappedComponent = withClaim(PageComponent);

    const wrapper = shallow(
      <WrappedComponent query={{ claim_id: "12345" }} appLogic={appLogic} />
    );

    expect(wrapper).toMatchInlineSnapshot(`
      <Spinner
        aria-valuetext="Loading claims"
      />
    `);
  });

  it("sets the 'claim' prop on the passed component to the claim identified in the query", () => {
    // Mock initial state of the app
    // these values would be passed from _app.js
    const id = "12345";
    const claim = new Claim({ application_id: id });
    const appLogic = useAppLogic();
    appLogic.claims = appLogic.claims.addItem(claim);

    // define component that needs a claim prop
    // eslint-disable-next-line react/prop-types
    const PageComponent = (props) => <div>{props.claim.application_id}</div>;

    // Wrap PageComponent in HOC
    const WrappedComponent = withClaim(PageComponent);

    // Mock query parameter that would be provided by next/router
    const query = { claim_id: id };

    const wrapper = mount(
      <WrappedComponent query={query} appLogic={appLogic} />
    );

    const pageComponent = wrapper.find("PageComponent");
    expect(pageComponent.prop("claim")).toEqual(claim);
    expect(appLogic.loadClaims).toHaveBeenCalledTimes(1);
  });
});
