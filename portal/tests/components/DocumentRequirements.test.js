import DocumentRequirements from "../../src/components/DocumentRequirements";
import React from "react";
import { shallow } from "enzyme";

describe("DocumentRequirements", () => {
  it("renders ID Document Requirements content", () => {
    const wrapper = shallow(<DocumentRequirements type="id" />);
    expect(wrapper.find("Heading")).toMatchSnapshot();
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });
  it("renders Certification Document Requirements content", () => {
    const wrapper = shallow(<DocumentRequirements type="certification" />);
    expect(wrapper.find("Heading")).toMatchSnapshot();
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });
});
