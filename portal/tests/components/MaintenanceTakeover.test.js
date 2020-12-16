import MaintenanceTakeover from "../../src/components/MaintenanceTakeover";
import React from "react";
import { shallow } from "enzyme";

describe("MaintenanceTakeover", () => {
  it("renders with the expected content", () => {
    const wrapper = shallow(<MaintenanceTakeover />);

    expect(wrapper).toMatchSnapshot();
  });
});
