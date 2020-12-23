import PreviousLeave, {
  PreviousLeaveReason,
} from "../../../src/models/PreviousLeave";
import AmendablePreviousLeave from "../../../src/components/employers/AmendablePreviousLeave";
import PreviousLeaves from "../../../src/components/employers/PreviousLeaves";
import React from "react";
import { shallow } from "enzyme";

describe("PreviousLeaves", () => {
  it("renders the component", () => {
    const previousLeaves = [
      new PreviousLeave({
        leave_start_date: "2020-03-01",
        leave_end_date: "2020-03-06",
        leave_reason: PreviousLeaveReason.serviceMemberFamily,
        previous_leave_id: 1,
      }),
      new PreviousLeave({
        leave_start_date: "2020-05-01",
        leave_end_date: "2020-05-10",
        leave_reason: PreviousLeaveReason.bonding,
        previous_leave_id: 2,
      }),
    ];
    const wrapper = shallow(
      <PreviousLeaves previousLeaves={previousLeaves} onChange={() => {}} />
    );

    expect(wrapper).toMatchSnapshot();
  });

  it("displays 'None reported' if no leave periods are reported", () => {
    const wrapper = shallow(
      <PreviousLeaves previousLeaves={[]} onChange={() => {}} />
    );

    expect(wrapper.find(AmendablePreviousLeave).exists()).toEqual(false);
    expect(wrapper.find("th").last().text()).toEqual("None reported");
  });
});
