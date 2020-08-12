import Claim from "../../src/models/Claim";
import React from "react";
import User from "../../src/models/User";
import merge from "lodash/merge";
import { renderWithAppLogic } from "../test-utils";
import useAppLogic from "../../src/hooks/useAppLogic";
import withClaim from "../../src/hoc/withClaim";

jest.mock("../../src/hooks/useAppLogic");

describe("withClaim", () => {
  let appLogic, claim_id, wrapper;

  function render(options = {}) {
    // define component that needs a claim prop
    // eslint-disable-next-line react/prop-types
    const PageComponent = (props) => <div>{props.claim.application_id}</div>;
    const WrappedComponent = withClaim(PageComponent);
    // Go three levels deep to get to PageComponent since withClaim is also wrapped by withClaims which is wrapped by withUser
    ({ wrapper } = renderWithAppLogic(
      WrappedComponent,
      merge(
        {
          diveLevels: 2,
          props: {
            appLogic,
            query: { claim_id },
          },
        },
        options
      )
    ));
  }

  beforeEach(() => {
    appLogic = useAppLogic();
    claim_id = "12345";
  });

  it("sets the 'claim' prop on the passed component to the claim identified in the query", () => {
    // Mock initial state of the app
    // these values would be passed from _app.js
    const claim = new Claim({ application_id: claim_id });
    appLogic.claims.claims = appLogic.claims.claims.addItem(claim);
    appLogic.user = new User();

    render();

    expect(wrapper.prop("claim")).toBeInstanceOf(Claim);
    expect(wrapper.prop("claim")).toEqual(claim);
  });

  it.todo("redirects to applications page if claim is not in claim collection");
});
