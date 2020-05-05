import Claim from "../../src/models/Claim";
import Collection from "../../src/models/Collection";
import React from "react";
import { shallow } from "enzyme";
import withClaim from "../../src/hoc/withClaim";

describe("WithClaim", () => {
  it("sets the 'claim' prop on the passed component to the claim identified in the query", () => {
    const idProperty = "claim_id";

    // Mock initial state of the app
    // these values would be passed from _app.js
    const id = "12345";
    const claim = new Claim({ claim_id: id });
    const itemsById = {
      [id]: claim,
    };
    const claims = new Collection({
      idProperty,
      itemsById,
    });

    // define component that needs a claim prop
    // eslint-disable-next-line react/prop-types
    const PageComponent = (props) => <div>{props.claim.claim_id}</div>;

    // Wrap PageComponent in HOC
    const WrappedComponent = withClaim(PageComponent);

    // Mock query parameter that would be provided by next/router
    const query = { [idProperty]: id };
    const wrapper = shallow(<WrappedComponent query={query} claims={claims} />);

    expect(wrapper.find("PageComponent").prop("claim")).toEqual(claim);
  });
});
