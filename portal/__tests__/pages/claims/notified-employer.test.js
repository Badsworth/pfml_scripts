import Claim from "../../../src/models/Claim";
import { NotifiedEmployer } from "../../../src/pages/claims/notified-employer";
import React from "react";
import routes from "../../../src/routes";
import { shallow } from "enzyme";

describe("NotifiedEmployer", () => {
  let claim, wrapper;
  const application_id = "12345";

  beforeEach(() => {
    claim = new Claim({ application_id });
    const query = { claim_id: claim.application_id };
    wrapper = shallow(
      <NotifiedEmployer claim={claim} query={query} appLogic={{}} />
    );
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("redirects to the review page", () => {
    expect(wrapper.find("QuestionPage").prop("nextPage")).toEqual(
      `${routes.claims.review}?claim_id=${claim.application_id}`
    );
  });
});
