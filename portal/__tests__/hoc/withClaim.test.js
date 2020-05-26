import Claim from "../../src/models/Claim";
import ClaimsApi from "../../src/api/ClaimsApi";
import Collection from "../../src/models/Collection";
import React from "react";
import User from "../../src/models/User";
import { shallow } from "enzyme";
import withClaim from "../../src/hoc/withClaim";

describe("WithClaim", () => {
  it("sets the 'claim' and 'claimsApi' prop on the passed component to the claim identified in the query", () => {
    const idProperty = "application_id";

    // Mock initial state of the app
    // these values would be passed from _app.js
    const id = "12345";
    const claim = new Claim({ application_id: id });
    const itemsById = {
      [id]: claim,
    };
    const claims = new Collection({
      idProperty,
      itemsById,
    });

    // define component that needs a claim prop
    // eslint-disable-next-line react/prop-types
    const PageComponent = (props) => <div>{props.claim.application_id}</div>;

    // Wrap PageComponent in HOC
    const WrappedComponent = withClaim(PageComponent);

    // Mock query parameter that would be provided by next/router
    const query = { claim_id: id };
    const wrapper = shallow(
      <WrappedComponent
        query={query}
        claims={claims}
        user={new User({ user_id: "1234" })}
      />
    );

    const pageComponent = wrapper.find("PageComponent");
    expect(pageComponent.prop("claim")).toEqual(claim);
    expect(pageComponent.prop("claimsApi")).toBeInstanceOf(ClaimsApi);
  });
});
