import HeadingPrefix from "../../src/components/HeadingPrefix";
import React from "react";
import { shallow } from "enzyme";

describe("HeadingPrefix", () => {
  it("renders span with expected classes", () => {
    const wrapper = shallow(<HeadingPrefix>Part 1</HeadingPrefix>);

    expect(wrapper).toMatchInlineSnapshot(`
      <span
        className="display-block font-heading-2xs margin-bottom-2 text-base-dark text-bold"
      >
        Part 1
      </span>
    `);
  });
});
