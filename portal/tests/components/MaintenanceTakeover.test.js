import MaintenanceTakeover from "../../src/components/MaintenanceTakeover";
import React from "react";
import { shallow } from "enzyme";

describe("MaintenanceTakeover", () => {
  it("renders the correct message text when start/end times are both provided", () => {
    const wrapper = shallow(
      <MaintenanceTakeover
        maintenanceStartTime="June 15, 2021, 3:00 PM EDT"
        maintenanceEndTime="June 17, 2021, 10:00 AM EDT"
      />
    );

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });

  it("renders the correct message text when only end time is provided", () => {
    const wrapper = shallow(
      <MaintenanceTakeover
        maintenanceStartTime={null}
        maintenanceEndTime="June 17, 2021, 10:00 AM EDT"
      />
    );

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });

  it("renders the correct message text when start/end times are not provided", () => {
    const wrapper = shallow(
      <MaintenanceTakeover
        maintenanceStartTime={null}
        maintenanceEndTime={null}
      />
    );

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });
});
