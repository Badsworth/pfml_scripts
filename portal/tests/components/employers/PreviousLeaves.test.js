import AmendablePreviousLeave from "../../../src/components/employers/AmendablePreviousLeave";
import PreviousLeaves from "../../../src/components/employers/PreviousLeaves";
import React from "react";
import { claim } from "../../test-utils";
import { shallow } from "enzyme";

describe("PreviousLeaves", () => {
  it("renders the component", () => {
    const wrapper = shallow(
      <PreviousLeaves previousLeaves={claim.previous_leaves} />
    );

    expect(wrapper).toMatchSnapshot();
  });

  it("displays 'None reported' if no leave periods are reported", () => {
    const wrapper = shallow(<PreviousLeaves previousLeaves={[]} />);

    expect(wrapper.find(AmendablePreviousLeave).exists()).toEqual(false);
    expect(wrapper.find("th").last().text()).toEqual("None reported");
  });
});
