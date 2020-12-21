import React from "react";
import UnsupportedBrowserBanner from "../../src/components/UnsupportedBrowserBanner";
import { shallow } from "enzyme";

describe("UnsupportedBrowserBanner", () => {
  it("renders inline styles and the banner message", () => {
    const wrapper = shallow(<UnsupportedBrowserBanner />);

    expect(wrapper.find("style")).toMatchSnapshot();
    expect(wrapper.find("span").html()).toMatchSnapshot();
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });

  it("excludes inline styles when forceRender prop is set", () => {
    const wrapper = shallow(<UnsupportedBrowserBanner forceRender />);

    expect(wrapper.find("style")).toMatchInlineSnapshot(`<style />`);
  });
});
