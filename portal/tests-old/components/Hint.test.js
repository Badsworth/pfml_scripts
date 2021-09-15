import Hint from "../../src/components/Hint";
import React from "react";
import { shallow } from "enzyme";

function render(customProps = {}) {
  const props = Object.assign(
    {
      children: "Hint text",
      inputId: "foo",
      small: false,
      className: null,
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

  it("does not set the `id` attribute when inputId is not set", () => {
    const { wrapper } = render({ inputId: undefined, children: "Text" });

    expect(wrapper.prop("id")).toBeNull();
  });

  it("adds className", () => {
    const { wrapper } = render({
      className: "margin-bottom-3",
      children: "Text",
    });

    expect(wrapper.find(".margin-bottom-3").exists()).toBe(true);
  });
});
