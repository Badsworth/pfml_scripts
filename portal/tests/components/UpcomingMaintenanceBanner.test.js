import React from "react";
import UpcomingMaintenanceBanner from "../../src/components/UpcomingMaintenanceBanner";
import { shallow } from "enzyme";

describe("MaintenanceTakeover", () => {
  it("Renders correct content when only start date is provided", () => {
    const wrapper = shallow(
      <UpcomingMaintenanceBanner start="June 15, 2021, 3:00 PM EDT" end="" />
    );

    expect(wrapper.find("Trans").first().dive()).toMatchSnapshot();
  });

  it("Renders correct content when only end date is provided", () => {
    const wrapper = shallow(
      <UpcomingMaintenanceBanner start="" end="June 17, 2021, 10:00 AM EDT" />
    );

    expect(wrapper.find("Trans").first().dive()).toMatchSnapshot();
  });

  it("Renders correct content when both start date and end date are provided", () => {
    const wrapper = shallow(
      <UpcomingMaintenanceBanner
        start="June 15, 2021, 3:00 PM EDT"
        end="June 17, 2021, 10:00 AM EDT"
      />
    );

    expect(wrapper.find("Trans").first().dive()).toMatchSnapshot();
  });

  it("Renders correct content when start date and end date are not provided", () => {
    const wrapper = shallow(<UpcomingMaintenanceBanner start="" end="" />);

    expect(wrapper.find("Trans").first().dive()).toMatchSnapshot();
  });
});
