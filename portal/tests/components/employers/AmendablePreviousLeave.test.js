import AmendButton from "../../../src/components/employers/AmendButton";
import AmendablePreviousLeave from "../../../src/components/employers/AmendablePreviousLeave";
import AmendmentForm from "../../../src/components/employers/AmendmentForm";
import React from "react";
import { claim } from "../../test-utils";
import { shallow } from "enzyme";

describe("AmendablePreviousLeave", () => {
  let wrapper;

  beforeEach(() => {
    wrapper = shallow(
      <AmendablePreviousLeave leavePeriod={claim.previous_leaves[0]} />
    );
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
