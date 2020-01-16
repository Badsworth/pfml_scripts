import Index from "../../pages/index";
import React from "react";
import { shallow } from "enzyme";

describe("Homepage", () => {
  // TODO: Remove this test once we're past the "Hello world" phase
  it("renders a hello world", () => {
    const wrapper = shallow(<Index />);

    expect(wrapper.html()).toContain("Hello, Mass PFML!");
  });
});
