import React from "react";
import TooltipIcon from "../../src/components/TooltipIcon";
import { shallow } from "enzyme";

describe("TooltipIcon", () => {
  it("renders the component", () => {
    const wrapper = shallow(
      <TooltipIcon position="bottom">Hello world</TooltipIcon>
    );

    expect(wrapper).toMatchInlineSnapshot(`
      <div
        className="usa-tooltip display-inline-block padding-05 text-middle text-base-dark"
        data-classes="text-normal"
        data-position="bottom"
        title="Hello world"
      >
        <Icon
          name="info"
        />
        <span
          className="usa-sr-only"
        >
          tip:
        </span>
      </div>
    `);
  });
});
