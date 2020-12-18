import BetaBanner from "../../src/components/BetaBanner";
import React from "react";
import { shallow } from "enzyme";

describe("BetaBanner", () => {
  it("renders message with given feedbackUrl", () => {
    const wrapper = shallow(<BetaBanner feedbackUrl="http://example.com" />);

    expect(wrapper.find("span")).toMatchSnapshot();
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });
});
