import AmendButton from "../../../src/components/employers/AmendButton";
import AmendablePreviousLeave from "../../../src/components/employers/AmendablePreviousLeave";
import AmendmentForm from "../../../src/components/employers/AmendmentForm";
import PreviousLeave from "../../../src/models/PreviousLeave";
import React from "react";
import { shallow } from "enzyme";

describe("AmendablePreviousLeave", () => {
  let previousLeave, wrapper;

  beforeEach(() => {
    previousLeave = new PreviousLeave({
      leave_start_date: "2020-03-01",
      leave_end_date: "2020-03-06",
      id: 1,
    });
    wrapper = shallow(<AmendablePreviousLeave leavePeriod={previousLeave} />);
  });

  it("renders the component", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("renders an AmendmentForm if user clicks on AmendButton", () => {
    wrapper.find(AmendButton).simulate("click");

    expect(wrapper.find(AmendmentForm).exists()).toEqual(true);
  });
});
