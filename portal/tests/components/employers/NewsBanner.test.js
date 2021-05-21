import { NewsBanner } from "../../../src/components/employers/NewsBanner";
import React from "react";
import { shallow } from "enzyme";

describe("NewsBanner", () => {
  it("renders the component", () => {
    const wrapper = shallow(<NewsBanner />);

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });
});
