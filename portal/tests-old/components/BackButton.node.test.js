/*
 * @jest-environment node
 */
import BackButton from "../../src/components/BackButton";
import React from "react";
import { shallow } from "enzyme";

describe("<BackButton> in Node server context", () => {
  it("does not render the back button when history API is undefined", () => {
    const wrapper = shallow(<BackButton />);
    expect(wrapper.isEmptyRender()).toBe(true);
  });
});
