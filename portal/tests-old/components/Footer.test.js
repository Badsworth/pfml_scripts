import Footer from "../../src/components/Footer";
import React from "react";
import { shallow } from "enzyme";

describe("Footer", () => {
  it("renders footer with default settings", () => {
    const wrapper = shallow(<Footer />);

    expect(wrapper).toMatchSnapshot();
  });
});
