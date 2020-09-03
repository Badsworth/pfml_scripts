import AmendLink from "../../../src/components/employers/AmendLink";
import React from "react";
import { shallow } from "enzyme";

describe("AmendLink", () => {
  it("renders the component", () => {
    const wrapper = shallow(<AmendLink />);

    expect(wrapper).toMatchSnapshot();
  });
});
