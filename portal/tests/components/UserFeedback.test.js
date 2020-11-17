import React from "react";
import UserFeedback from "../../src/components/UserFeedback";
import { shallow } from "enzyme";

describe("UserFeedback", () => {
  it("renders the component", () => {
    const wrapper = shallow(<UserFeedback url="https://example.com" />);

    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });
});
