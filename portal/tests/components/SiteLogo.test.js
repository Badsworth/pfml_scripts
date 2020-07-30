import React from "react";
import SiteLogo from "../../src/components/SiteLogo";
import { shallow } from "enzyme";

describe("SiteLogo", () => {
  it("renders site-wide logo", () => {
    const wrapper = shallow(<SiteLogo />);

    expect(wrapper).toMatchSnapshot();
  });
});
