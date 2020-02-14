import FormLabel from "../../src/components/FormLabel";
import React from "react";
import { shallow } from "enzyme";

function render(customProps = {}) {
  const props = Object.assign(
    {
      children: "Field Label"
    },
    customProps
  );

  const component = <FormLabel {...props} />;

  return {
    props,
    wrapper: shallow(component)
  };
}

describe("FormLabel", () => {
  it("defaults to a label element", () => {
    const { wrapper } = render();
    const label = wrapper.find(".usa-label");

    expect(label.is("label")).toBe(true);
  });

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

  describe("when component prop is set to legend", () => {
    it("renders a legend element", () => {
      const { wrapper } = render({ component: "legend" });
      const label = wrapper.find(".usa-label");

      expect(label.is("legend")).toBe(true);
    });
  });

  describe("when hint prop is set", () => {
    it("renders the hint text", () => {
      const { props, wrapper } = render({ hint: "123" });
      const node = wrapper.find(".usa-hint").last();

      expect(node.text()).toBe(props.hint);
    });
  });

  describe("when optionalText prop is set", () => {
    it("renders the optionalText", () => {
      const { props, wrapper } = render({ optionalText: "(optional)" });
      const node = wrapper.find(".usa-hint").first();

      expect(node.text()).toMatch(props.optionalText);
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
});
