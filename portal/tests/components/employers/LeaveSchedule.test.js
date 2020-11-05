import IntermittentLeaveSchedule from "../../../src/components/employers/IntermittentLeaveSchedule";
import LeaveSchedule from "../../../src/components/employers/LeaveSchedule";
import { MockEmployerClaimBuilder } from "../../test-utils";
import React from "react";
import { shallow } from "enzyme";

describe("LeaveSchedule", () => {
  it("renders reduced schedule", () => {
    const claim = new MockEmployerClaimBuilder().reducedSchedule().create();
    const wrapper = shallow(<LeaveSchedule claim={claim} />);

    expect(wrapper).toMatchSnapshot();
  });

  it("renders intermittent schedule", () => {
    const claim = new MockEmployerClaimBuilder().intermittent().create();
    const wrapper = shallow(<LeaveSchedule claim={claim} />);

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find(IntermittentLeaveSchedule).exists()).toEqual(true);
  });
});
