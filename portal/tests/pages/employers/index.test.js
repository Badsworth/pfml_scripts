import Index from "../../../src/pages/employers/index";
import React from "react";
import { shallow } from "enzyme";

describe("Index", () => {
  let wrapper;

  beforeEach(() => {
    wrapper = shallow(<Index />);
  });

  it("renders dashboard content", () => {
    expect(wrapper).toMatchSnapshot();
  });
});
