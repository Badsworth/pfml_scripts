import LeaveSchedule from "../../../src/components/employers/LeaveSchedule";
import React from "react";
import { claim } from "../../test-utils";
import { shallow } from "enzyme";

describe("LeaveSchedule", () => {
  it("renders the component", () => {
    const wrapper = shallow(<LeaveSchedule claim={claim} />);

    expect(wrapper).toMatchSnapshot();
  });
});
