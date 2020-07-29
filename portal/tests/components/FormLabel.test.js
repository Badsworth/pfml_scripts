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

  describe("when hint prop is set", () => {
    describe("and the hint is a string", () => {
      it("styles the hint text with hint classes", () => {
        const { wrapper } = render({ hint: "Hint text" });
        const hint = wrapper.find(".usa-hint").last();

        expect(hint).toMatchInlineSnapshot(`
          <span
            className="display-block line-height-sans-5 usa-hint margin-top-05"
          >
            Hint text
          </span>
        `);
      });
    });

    describe("and the hint is not a string", () => {
      it("does not style the hint", () => {
        const hintElement = <p>Hint paragraph</p>;
        const { wrapper } = render({ hint: hintElement });
        const hint = wrapper.find("span").last();

        expect(hint).toMatchInlineSnapshot(`
          <span
            className="margin-top-05"
          >
            <p>
              Hint paragraph
            </p>
          </span>
        `);
      });
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

    it("doesn't include a margin on hint text", () => {
      const { wrapper } = render({ small: true, hint: "Hint text" });

      const hint = wrapper.find(".usa-hint").last();

      expect(hint.prop("className")).toMatchInlineSnapshot(
        `"display-block line-height-sans-5 usa-hint"`
      );
    });
  });
});
