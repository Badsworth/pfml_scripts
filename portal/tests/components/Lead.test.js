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
});
