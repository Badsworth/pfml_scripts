import ButtonLink from "../../src/components/ButtonLink";
import React from "react";
import { shallow } from "enzyme";

function render(customProps = {}) {
  const props = Object.assign(
    {
      children: "Button label",
      href: "http://www.example.com",
    },
    customProps
  );

  const component = <ButtonLink {...props} />;

  return {
    props,
    wrapper: shallow(component),
  };
}

describe("ButtonLink", () => {
  it("renders with default styling", () => {
    const { wrapper } = render();

    expect(wrapper).toMatchInlineSnapshot(`
      <Link
        href="http://www.example.com"
      >
        <a
          className="usa-button"
        >
          Button label
        </a>
      </Link>
    `);
  });

  it("accepts a variation property", () => {
    const { wrapper } = render({ variation: "outline" });
    const anchor = wrapper.find("a");

    expect(anchor.hasClass("usa-button--outline")).toBe(true);
  });

  describe("when className is set", () => {
    it("adds the className to the link", () => {
      const { wrapper } = render({ className: "custom-class" });
      const anchor = wrapper.find("a");

      expect(anchor.hasClass("custom-class")).toBe(true);
    });
  });

  describe("when disabled is true", () => {
    it("it renders a button with disabled attribute and style", () => {
      const { wrapper } = render({ disabled: true });

      expect(wrapper.find("button").prop("disabled")).toBe(true);
      expect(wrapper.find("button").hasClass("disabled")).toBe(true);
    });
  });
});
