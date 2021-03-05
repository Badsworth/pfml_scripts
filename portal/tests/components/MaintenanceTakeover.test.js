import MaintenanceTakeover from "../../src/components/MaintenanceTakeover";
import React from "react";
import { shallow } from "enzyme";

describe("MaintenanceTakeover", () => {
  it("renders with the expected content", () => {
    const wrapper = shallow(<MaintenanceTakeover />);

    expect(wrapper).toMatchSnapshot();
  });

  it("renders scheduled text when scheduledRemovalDayAndTimeText prop is set", () => {
    const wrapper = shallow(
      <MaintenanceTakeover scheduledRemovalDayAndTimeText="Sunday, March 7th at 10:00 p.m. EST" />
    );
    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });
});
