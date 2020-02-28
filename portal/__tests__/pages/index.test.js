import "../../src/i18n";
import Index from "../../src/pages/index";
import React from "react";
import { shallow } from "enzyme";

describe("Index", () => {
  it("renders the page", () => {
    const wrapper = shallow(<Index />);

    expect(wrapper).toMatchSnapshot();
  });
});
