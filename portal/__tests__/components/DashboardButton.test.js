import "../../src/i18n";
import { mount, shallow } from "enzyme";
import DashboardButton from "../../src/components/DashboardButton";
import React from "react";

describe("DashboardButton", () => {
  it("directs user to the dashboard", () => {
    const wrapper = shallow(<DashboardButton />);

    expect(wrapper.prop("href")).toEqual("/");
  });

  it("accepts a variation property", () => {
    const wrapper = mount(<DashboardButton variation="outline" />);
    const anchor = wrapper.find("a");

    expect(anchor.hasClass("usa-button--outline")).toBe(true);
  });
});
