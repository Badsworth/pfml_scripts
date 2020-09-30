import LeaveSchedule from "../../../src/components/employers/LeaveSchedule";
import { MockClaimBuilder } from "../../test-utils";
import React from "react";
import { shallow } from "enzyme";

describe("LeaveSchedule", () => {
  it("renders the component", () => {
    const claim = new MockClaimBuilder().reducedSchedule().submitted().create();
    const wrapper = shallow(<LeaveSchedule claim={claim} />);

    expect(wrapper).toMatchSnapshot();
  });
});
