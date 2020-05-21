import Claim from "../../../src/models/Claim";
import { NotifiedEmployer } from "../../../src/pages/claims/notified-employer";
import React from "react";
import routes from "../../../src/routes";
import { shallow } from "enzyme";

describe("NotifiedEmployer", () => {
  let claim, wrapper;
  const claim_id = "12345";

  beforeEach(() => {
    claim = new Claim({ claim_id });
    wrapper = shallow(<NotifiedEmployer claim={claim} />);
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("redirects to the todo page for now", () => {
    expect(wrapper.find("QuestionPage").prop("nextPage")).toEqual(
      routes.claims.todo
    );
  });
});
