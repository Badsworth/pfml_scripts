import DashboardNavigation from "../../src/components/DashboardNavigation";
import React from "react";
import { shallow } from "enzyme";

describe("DashboardNavigation", () => {
  it("renders dashboard links", () => {
    const wrapper = shallow(<DashboardNavigation activeHref="/dashboard" />);

    expect(wrapper).toMatchSnapshot();
  });
});
