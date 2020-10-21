import IntermittentLeaveSchedule from "../../../src/components/employers/IntermittentLeaveSchedule";
import LeaveSchedule from "../../../src/components/employers/LeaveSchedule";
import { MockClaimBuilder } from "../../test-utils";
import React from "react";
import { shallow } from "enzyme";

describe("LeaveSchedule", () => {
  it("renders reduced schedule", () => {
    const claim = new MockClaimBuilder().reducedSchedule().submitted().create();
    const wrapper = shallow(<LeaveSchedule claim={claim} />);

    expect(wrapper).toMatchSnapshot();
  });

  it("renders intermittent schedule", () => {
    const claim = new MockClaimBuilder().intermittent().submitted().create();
    const wrapper = shallow(<LeaveSchedule claim={claim} />);

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find(IntermittentLeaveSchedule).exists()).toEqual(true);
  });
});
