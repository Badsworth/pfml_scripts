import FormLabel from "../../src/components/FormLabel";
import React from "react";
import { shallow } from "enzyme";

function render(customProps = {}) {
  const props = Object.assign(
    {
      children: "Field Label",
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
      const { wrapper } = render({ component: "label" });

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when hint prop is set", () => {
    it("styles the hint as usa-intro", () => {
      const { wrapper } = render({ hint: "Hint text" });
      const hint = wrapper.find(".usa-intro").last();

      expect(hint).toMatchInlineSnapshot(`
        <span
          className="display-block line-height-sans-5 margin-top-2 usa-intro"
        >
          Hint text
        </span>
      `);
    });

    describe("when the label is small", () => {
      it("styles the hint text as usa-hint", () => {
        const { wrapper } = render({ hint: "Hint text", small: true });
        const hint = wrapper.find(".usa-hint").last();

        expect(hint).toMatchInlineSnapshot(`
          <span
            className="display-block line-height-sans-5 margin-top-2 usa-hint"
          >
            Hint text
          </span>
        `);
      });
    });
  });

  describe("when example prop is set", () => {
    it("it renders the example text with expected classes", () => {
      const { wrapper } = render({ example: "Example text" });
      const example = wrapper.find(".usa-hint").last();

      expect(example).toMatchInlineSnapshot(`
        <span
          className="display-block line-height-sans-5 margin-top-2 usa-hint"
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
          className="usa-hint text-normal"
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
        `"usa-label maxw-none"`
      );
    });

    it("adds classes for a smaller type size to the legend", () => {
      const { wrapper } = render({ small: true, component: "legend" });

      const label = wrapper.find(".usa-label");

      expect(label.prop("className")).toMatchInlineSnapshot(
        `"usa-label maxw-none usa-legend font-heading-sm"`
      );
    });
  });
});
