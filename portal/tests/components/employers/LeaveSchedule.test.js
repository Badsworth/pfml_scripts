import { MockClaimBuilder, claim } from "../../test-utils";
import LeaveSchedule from "../../../src/components/employers/LeaveSchedule";
import React from "react";
import { shallow } from "enzyme";

describe("LeaveSchedule", () => {
  it("renders the component", () => {
    const wrapper = shallow(<LeaveSchedule claim={claim} />);

    expect(wrapper).toMatchSnapshot();
  });

  it("displays only leave types applicable to claim", () => {
    const claimWithContinuousOnly = new MockClaimBuilder()
      .reducedSchedule({
        leave_period_id: 1,
        hours_per_week: 5,
        weeks: 12,
      })
      .leaveDuration()
      .create();
    const wrapper = shallow(<LeaveSchedule claim={claimWithContinuousOnly} />);

    expect(wrapper.find(".continuous")).toHaveLength(0);
    expect(wrapper.find(".intermittent")).toHaveLength(0);
    expect(wrapper.find(".reduced")).toHaveLength(1);
  });
});
