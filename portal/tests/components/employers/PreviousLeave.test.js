import AmendButton from "../../../src/components/employers/AmendButton";
import AmendmentForm from "../../../src/components/employers/AmendmentForm";
import PreviousLeave from "../../../src/components/employers/PreviousLeave";
import React from "react";
import { claim } from "../../test-utils";
import { shallow } from "enzyme";

describe("PreviousLeave", () => {
  let wrapper;

  beforeEach(() => {
    wrapper = shallow(<PreviousLeave leavePeriod={claim.previous_leaves[0]} />);
  });

  it("renders the component", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("renders an AmendmentForm if user clicks on AmendButton", () => {
    expect(wrapper.find(AmendmentForm).exists()).toEqual(false);
    wrapper.find(AmendButton).simulate("click");
    expect(wrapper.find(AmendmentForm).exists()).toEqual(true);
  });
});
