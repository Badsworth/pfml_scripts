import Claim from "../../../src/models/Claim";
import { LeaveType } from "../../../src/pages/claims/leave-type";
import React from "react";
import { shallow } from "enzyme";

describe("LeaveType", () => {
  it("renders the page", () => {
    const wrapper = shallow(
      <LeaveType claim={new Claim({ application_id: "12345" })} />
    );
    expect(wrapper).toMatchSnapshot();
  });
});
