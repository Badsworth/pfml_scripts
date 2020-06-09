import Claim from "../../../src/models/Claim";
import React from "react";
import { Review } from "../../../src/pages/claims/review";
import { shallow } from "enzyme";

describe("Review", () => {
  it("renders Review page", () => {
    const claim = new Claim({
      application_id: "mock-id",
      duration_type: "continuous",
      leave_start_date: "2021-09-01",
      leave_end_date: "2021-12-30",
    });
    const query = { claim_id: claim.application_id };

    const wrapper = shallow(<Review claim={claim} query={query} />);

    expect(wrapper).toMatchSnapshot();
  });
});
