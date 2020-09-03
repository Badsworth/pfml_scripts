import PastLeave from "../../../src/components/employers/PastLeave";
import React from "react";
import { claim } from "../../test-utils";
import { shallow } from "enzyme";

describe("PastLeave", () => {
  let wrapper;

  beforeEach(() => {
    wrapper = shallow(<PastLeave previousLeaves={claim.previous_leaves} />);
  });

  it("renders the component", () => {
    expect(wrapper).toMatchSnapshot();
  });
});
