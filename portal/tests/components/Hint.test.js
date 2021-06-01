import Hint from "../../src/components/Hint";
import React from "react";
import { shallow } from "enzyme";

function render(customProps = {}) {
  const props = Object.assign(
    {
      children: "Hint text",
      inputId: "foo",
      small: false,
    },
    customProps
  );

  const component = <Hint {...props} />;

  return {
    props,
    wrapper: shallow(component),
  };
}

describe("Hint", () => {
  it("renders usa-intro by default", () => {
    const { wrapper } = render({ children: "This is the hint" });

    expect(wrapper).toMatchInlineSnapshot(`
      <span
        className="display-block line-height-sans-5 measure-5 usa-intro"
        id="foo_hint"
      >
        This is the hint
      </span>
    `);
  });

  it("renders usa-hint when small prop is set to true", () => {
    const { wrapper } = render({ children: "This is the hint", small: true });

    expect(wrapper).toMatchInlineSnapshot(`
      <span
        className="display-block line-height-sans-5 measure-5 usa-hint text-base-darkest"
        id="foo_hint"
      >
        This is the hint
      </span>
    `);
  });

  it("generates id if no inputId is passed", () => {
    const { wrapper } = render({ inputId: undefined, children: "Text" });
    const hint = wrapper.find(".usa-intro");

    expect(hint.prop("id")).not.toBe("undefined_hint");
  });
});
