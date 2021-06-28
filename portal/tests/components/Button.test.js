import Button from "../../src/components/Button";
import React from "react";
import { shallow } from "enzyme";

function render(customProps = {}) {
  const props = Object.assign(
    {
      children: "Button label",
      onClick: jest.fn(),
    },
    customProps
  );

  const component = <Button {...props} />;

  return {
    props,
    wrapper: shallow(component),
  };
}

describe("Button", () => {
  it("renders with default styling", () => {
    const { wrapper } = render();

    expect(wrapper).toMatchInlineSnapshot(`
      <Fragment>
        <button
          className="usa-button position-relative"
          onClick={[MockFunction]}
          type="button"
        >
          Button label
        </button>
      </Fragment>
    `);
  });

  it("accepts a variation property", () => {
    const { wrapper } = render({ variation: "outline" });

    expect(wrapper.find("button").hasClass("usa-button--outline")).toBe(true);
  });

  describe("when className is set", () => {
    it("adds the className to the button", () => {
      const { wrapper } = render({ className: "custom-class" });

      expect(wrapper.find("button").hasClass("custom-class")).toBe(true);
    });
  });

  describe("when inversed prop is true", () => {
    it("adds the inversed modifier class", () => {
      const { wrapper } = render({ inversed: true });

      expect(wrapper.find("button").hasClass("usa-button--inverse")).toBe(true);
    });
  });

  describe("when inversed prop is true and the variation is 'unstyled'", () => {
    it("adds the outline modifier class", () => {
      const { wrapper } = render({ inversed: true, variation: "unstyled" });

      expect(wrapper.find("button").hasClass("usa-button--outline")).toBe(true);
    });
  });

  describe("when loading is set", () => {
    it("disables button and adds a spinner", () => {
      const { wrapper } = render({ loading: true });

      expect(wrapper.find("Spinner").exists()).toBe(true);
      expect(wrapper.find("button").prop("disabled")).toBe(true);
    });

    it("sets minimum height when variation is unstyled", () => {
      const { wrapper } = render({ loading: true, variation: "unstyled" });

      expect(wrapper.find("button").hasClass("minh-5")).toBe(true);
    });

    it("renders a message when loadingMessage is set", () => {
      const { wrapper } = render({
        loading: true,
        loadingMessage: "Saving… please wait.",
      });

      expect(wrapper.find("strong")).toMatchInlineSnapshot(`
        <strong
          className="display-block mobile-lg:display-inline-block margin-top-1 mobile-lg:margin-top-0 text-center mobile-lg:text-left"
        >
          Saving… please wait.
        </strong>
      `);
    });
  });

  it("accepts aria props", () => {
    const { wrapper } = render({
      "aria-controls": "foo",
      "aria-expanded": "false",
    });

    const button = wrapper.find("button");

    expect(button.prop("aria-controls")).toBe("foo");
    expect(button.prop("aria-expanded")).toBe("false");
  });
});
