import LeaveType from "../../../src/pages/claims/leave-type";
import React from "react";
import { shallow } from "enzyme";

describe("LeaveType", () => {
  it("renders the page", () => {
    const wrapper = shallow(<LeaveType />);
    expect(wrapper).toMatchSnapshot();
  });
});
