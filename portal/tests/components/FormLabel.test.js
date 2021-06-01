import FormLabel from "../../src/components/FormLabel";
import React from "react";
import { shallow } from "enzyme";

function render(customProps = {}) {
  const props = Object.assign(
    {
      children: "Field Label",
      inputId: "foo",
    },
    customProps
  );

  const component = <FormLabel {...props} />;

  return {
    props,
    wrapper: shallow(component),
  };
}

describe("FormLabel", () => {
  it("renders the component children as the label's text", () => {
    const text = "Foo Bar";
    const { wrapper } = render({ children: text });
    const label = wrapper.find(".usa-label");

    expect(label.text()).toMatch(text);
  });

  it("uses inputId as the label's `for` attribute", () => {
    const inputId = "foo";
    const { wrapper } = render({ inputId });
    const field = wrapper.find(".usa-label");

    expect(field.prop("htmlFor")).toBe(inputId);
  });

  describe("when the type prop isn't set", () => {
    it("renders label with expected classes", () => {
      const { wrapper } = render();

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when component prop is set to legend", () => {
    it("renders legend with expected classes", () => {
      const { wrapper } = render({ component: "legend" });

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when component prop is set to label", () => {
    it("renders label with expected classes", () => {
      const { wrapper } = render({ component: "label", inputId: "foo" });

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when hint prop is set", () => {
    it("renders the hint", () => {
      const { wrapper } = render({ hint: "Hint text" });
      const hint = wrapper.find("Hint").last();

      expect(hint).toMatchInlineSnapshot(`
        <Hint
          inputId="foo"
          small={false}
        >
          Hint text
        </Hint>
      `);
    });

    describe("when the label is small", () => {
      it("passes small prop to Hint", () => {
        const { wrapper } = render({ hint: "Hint text", small: true });
        const hint = wrapper.find("Hint");

        expect(hint.prop("small")).toBe(true);
      });
    });
  });

  describe("when example prop is set", () => {
    it("it renders the example text with expected classes", () => {
      const { wrapper } = render({ example: "Example text" });
      const example = wrapper.find(".usa-hint").last();

      expect(example).toMatchInlineSnapshot(`
        <span
          className="display-block line-height-sans-5 usa-hint text-base-dark measure-5"
        >
          Example text
        </span>
      `);
    });
  });

  describe("when optionalText prop is set", () => {
    it("renders the optional text with expected classes", () => {
      const { wrapper } = render({ optionalText: "(optional)" });
      const node = wrapper.find(".usa-label .usa-hint").first();

      expect(node).toMatchInlineSnapshot(`
        <span
          className="usa-hint text-base-dark text-normal"
        >
           (optional)
        </span>
      `);
    });
  });

  describe("when errorMsg is set", () => {
    it("renders the errorMsg", () => {
      const { props, wrapper } = render({ errorMsg: "Oh no." });
      const node = wrapper.find(".usa-error-message");

      expect(node.text()).toBe(props.errorMsg);
      expect(node.prop("role")).toBe("alert");
      expect(node.prop("id")).toBeDefined();
    });

    it("adds error classes to the label", () => {
      const { wrapper } = render({ errorMsg: "Oh no." });
      const label = wrapper.find(".usa-label");

      expect(label.hasClass("usa-label--error")).toBe(true);
    });
  });

  describe("when `small` is true", () => {
    it("adds classes for a smaller type size to the label", () => {
      const { wrapper } = render({ small: true });

      const label = wrapper.find(".usa-label");

      expect(label.prop("className")).toMatchInlineSnapshot(
        `"usa-label text-bold font-heading-xs measure-5"`
      );
    });

    it("adds classes for a smaller type size to the legend", () => {
      const { wrapper } = render({ small: true, component: "legend" });

      const label = wrapper.find(".usa-label");

      expect(label.prop("className")).toMatchInlineSnapshot(
        `"usa-label text-bold usa-legend font-heading-xs measure-5"`
      );
    });
  });

  describe("when `labelClassName` is set", () => {
    it("overrides the .text-bold class", () => {
      const { wrapper } = render({ labelClassName: "text-normal" });
      const label = wrapper.find(".usa-label");

      expect(label.hasClass("text-normal")).toBe(true);
      expect(label.hasClass("text-bold")).toBe(false);
    });
  });
});
