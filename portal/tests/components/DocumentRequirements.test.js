import DocumentRequirements from "../../src/components/DocumentRequirements";
import React from "react";
import { shallow } from "enzyme";

describe("DocumentRequirements", () => {
  const wrapper = shallow(<DocumentRequirements />);
  it("renders Document Requirements content", () => {
    expect(wrapper.find("Heading")).toMatchSnapshot();
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });
});
