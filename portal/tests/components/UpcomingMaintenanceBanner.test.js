import React from "react";
import UpcomingMaintenanceBanner from "../../src/components/UpcomingMaintenanceBanner";
import { shallow } from "enzyme";

describe("MaintenanceTakeover", () => {
  it("Renders correct content when only start date is provided", () => {
    const wrapper = shallow(<UpcomingMaintenanceBanner start="June 15, 2021, 3:00 PM EDT" end="" />);

    expect(wrapper).toMatchSnapshot();
  });

  it("Renders correct content when both start date and end date are provided", () => {
    const wrapper = shallow(<UpcomingMaintenanceBanner start="June 15, 2021, 3:00 PM EDT" end="June 17, 2021, 10:00 AM EDT" />);

    expect(wrapper).toMatchSnapshot();
  });
});
