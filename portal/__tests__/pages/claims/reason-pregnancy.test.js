import Claim from "../../../src/models/Claim";
import React from "react";
import { ReasonPregnancy } from "../../../src/pages/claims/reason-pregnancy";
import { shallow } from "enzyme";

describe("ReasonPregnancy", () => {
  it("renders the page", () => {
    const claim = new Claim({
      application_id: "12345",
      pregnant_or_recent_birth: false,
    });
    const wrapper = shallow(<ReasonPregnancy claim={claim} appLogic={{}} />);
    expect(wrapper).toMatchSnapshot();
  });
});
