import React from "react";
import UnsupportedBrowserBanner from "../../src/components/UnsupportedBrowserBanner";
import { shallow } from "enzyme";

describe("UnsupportedBrowserBanner", () => {
  it("renders conditional HTML comment and the banner message", () => {
    const wrapper = shallow(<UnsupportedBrowserBanner />);

    expect(wrapper.find("span").html()).toMatchSnapshot();
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });

  it("adds display-block when forceRender prop is set", () => {
    const wrapper = shallow(<UnsupportedBrowserBanner forceRender />);

    expect(wrapper.find(".display-block").exists()).toBe(true);
  });
});
