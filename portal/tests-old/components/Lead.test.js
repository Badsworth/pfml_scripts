import Lead from "../../src/components/Lead";
import React from "react";
import { shallow } from "enzyme";

describe("Lead", () => {
  it("renders a paragraph with intro class", () => {
    const wrapper = shallow(<Lead>Hello world</Lead>);

    expect(wrapper).toMatchInlineSnapshot(`
      <p
        className="usa-intro"
      >
        Hello world
      </p>
    `);
  });

  it("adds additional class names", () => {
    const wrapper = shallow(<Lead className="margin-top-6">Hello world</Lead>);

    expect(wrapper.hasClass("margin-top-6")).toBe(true);
    // Still has default classes
    expect(wrapper.hasClass("usa-intro")).toBe(true);
  });
});
