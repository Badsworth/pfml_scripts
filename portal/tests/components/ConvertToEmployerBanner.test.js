import ConvertToEmployerBanner from "../../src/components/ConvertToEmployerBanner";
import React from "react";
import { shallow } from "enzyme";

describe("ConvertToEmployerBanner", () => {
  it("renders HTML comment and the banner message", () => {
    const wrapper = shallow(<ConvertToEmployerBanner />);
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });
});
