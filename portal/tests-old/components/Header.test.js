import User, { RoleDescription, UserRole } from "../../src/models/User";
import { DateTime } from "luxon";
import Header from "../../src/components/Header";
import React from "react";
import { shallow } from "enzyme";

describe("Header", () => {
  it("includes a Skip Nav link as its first link", () => {
    const wrapper = shallow(<Header onLogout={jest.fn()} />);

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find(".usa-skipnav").props().href).toBe("#main");
  });

  it("renders Header for logged in claimant", () => {
    const user = new User({
      email_address: "email@address.com",
      user_id: "mock-user-id",
    });

    const wrapper = shallow(<Header user={user} onLogout={jest.fn()} />);

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("HeaderSlim").prop("utilityNav").props.user).toBe(user);
  });

  it("doesn't render beta banner when user isn't logged in", () => {
    const wrapper = shallow(<Header onLogout={jest.fn()} />);

    expect(wrapper.find("BetaBanner").exists()).toBe(false);
  });

  it("renders beta banner with employer feedback link when user is an employer", () => {
    const user = new User({
      email_address: "email@address.com",
      user_id: "mock-user-id",
      roles: [
        new UserRole({
          role_description: RoleDescription.employer,
        }),
      ],
    });
    const wrapper = shallow(<Header user={user} onLogout={jest.fn()} />);

    expect(
      wrapper.find("BetaBanner").prop("feedbackUrl")
    ).toMatchInlineSnapshot(
      `"https://www.mass.gov/paidleave-employer-feedback"`
    );
  });

  it("doesn't render maintenance alert bar when maintenance is disabled", () => {
    const wrapper = shallow(
      <Header showUpcomingMaintenanceAlertBar={false} onLogout={jest.fn()} />
    );
    expect(wrapper.find("AlertBar").exists()).toBe(false);
  });

  it("renders maintenance alert bar when maintenance is enabled and start/end times are both provided", () => {
    // Starts in an hour ago
    const maintenanceStart = DateTime.local()
      .plus({ hours: 1 })
      .toLocaleString(DateTime.DATETIME_FULL);
    // Ends in 2 hours
    const maintenanceEnd = DateTime.local()
      .plus({ hours: 2 })
      .toLocaleString(DateTime.DATETIME_FULL);

    const wrapper = shallow(
      <Header
        showUpcomingMaintenanceAlertBar={true}
        maintenanceStartTime={maintenanceStart}
        maintenanceEndTime={maintenanceEnd}
        onLogout={jest.fn()}
      />
    );
    expect(wrapper.find("AlertBar").exists()).toBe(true);
  });

  it("doesn't render maintenance alert bar when maintenance is enabled and only end time is provided", () => {
    // Ends in 2 hours
    const maintenanceEnd = DateTime.local()
      .plus({ hours: 2 })
      .toLocaleString(DateTime.DATETIME_FULL);

    const wrapper = shallow(
      <Header
        showUpcomingMaintenanceAlertBar={true}
        maintenanceEndTime={maintenanceEnd}
        onLogout={jest.fn()}
      />
    );
    expect(wrapper.find("AlertBar").exists()).toBe(false);
  });

  it("renders maintenance alert bar when maintenance is enabled and only start time is provided", () => {
    // Starts in an hour ago
    const maintenanceStart = DateTime.local()
      .plus({ hours: 1 })
      .toLocaleString(DateTime.DATETIME_FULL);

    const wrapper = shallow(
      <Header
        showUpcomingMaintenanceAlertBar={true}
        maintenanceStartTime={maintenanceStart}
        onLogout={jest.fn()}
      />
    );
    expect(wrapper.find("AlertBar").exists()).toBe(true);
  });

  it("renders the correct maintenance alert text when start/end times are both provided", () => {
    const maintenanceStart = "June 15, 2021, 3:00 PM EDT";
    const maintenanceEnd = "June 17, 2021, 10:00 AM EDT";

    const wrapper = shallow(
      <Header
        showUpcomingMaintenanceAlertBar={true}
        maintenanceStartTime={maintenanceStart}
        maintenanceEndTime={maintenanceEnd}
        onLogout={jest.fn()}
      />
    );
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });

  it("renders the correct maintenance alert text when only start time is provided", () => {
    const maintenanceStart = "June 15, 2021, 3:00 PM EDT";

    const wrapper = shallow(
      <Header
        showUpcomingMaintenanceAlertBar={true}
        maintenanceStartTime={maintenanceStart}
        maintenanceEndTime={null}
        onLogout={jest.fn()}
      />
    );
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });
});
