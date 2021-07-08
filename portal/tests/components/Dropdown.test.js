import Dropdown from "../../src/components/Dropdown";
import React from "react";
import { shallow } from "enzyme";

function render(customProps = {}) {
  const props = Object.assign(
    {
      choices: [
        {
          label: "Apple",
          value: "a",
        },
        {
          label: "Banana",
          value: "b",
        },
      ],
      emptyChoiceLabel: "Select an answer",
      label: "Field Label",
      name: "field-name",
      onChange: jest.fn(),
    },
    customProps
  );

  const component = <Dropdown {...props} />;

  return {
    props,
    wrapper: shallow(component),
  };
}

describe("Dropdown", () => {
  it("renders select field with list of options", () => {
    const { wrapper } = render();

    expect(wrapper.exists(".usa-combo-box")).toBe(false);
    expect(wrapper.find("select")).toMatchSnapshot();
  });

  it("sets the field's name", () => {
    const name = "foo";
    const { wrapper } = render({ name });
    const field = wrapper.find(".usa-select");

    expect(field.prop("name")).toBe(name);
  });

  it("sets the field's value", () => {
    const value = "Yay";
    const { wrapper } = render({ value });
    const field = wrapper.find(".usa-select");

    expect(field.prop("value")).toBe(value);
  });

  it("generates a unique id", () => {
    const { wrapper: wrapper1 } = render({ name: "one" });
    const { wrapper: wrapper2 } = render({ name: "two" });

    const input1 = wrapper1.find(".usa-select");
    const label1 = wrapper1.find("FormLabel");
    const input2 = wrapper2.find(".usa-select");

    const idRegex = /Dropdown[0-9]+/;

    expect(input1.prop("id")).toMatch(idRegex);
    expect(input1.prop("id")).not.toBe(input2.prop("id"));
    expect(label1.prop("inputId")).toBe(input1.prop("id"));
  });

  it("renders a label component", () => {
    const { props, wrapper } = render();
    const label = wrapper.find("FormLabel");

    expect(label.prop("children")).toBe(props.label);
  });

  describe("when hint prop is set", () => {
    it("passes the hint to FormLabel", () => {
      const { props, wrapper } = render({ hint: "123" });
      const label = wrapper.find("FormLabel");

      expect(label.prop("hint")).toBe(props.hint);
    });
  });

  describe("when optionalText prop is set", () => {
    it("passes the optionalText to FormLabel", () => {
      const { props, wrapper } = render({ optionalText: "(optional)" });
      const label = wrapper.find("FormLabel");

      expect(label.prop("optionalText")).toBe(props.optionalText);
    });
  });

  describe("when errorMsg is set", () => {
    it("passes errorMsg to FormLabel", () => {
      const { props, wrapper } = render({ errorMsg: "Oh no." });

      expect(wrapper.find("FormLabel").prop("errorMsg")).toBe(props.errorMsg);
    });

    it("adds error classes to the form group", () => {
      const { wrapper } = render({ errorMsg: "Oh no." });
      const formGroup = wrapper.find(".usa-form-group");

      expect(formGroup.hasClass("usa-form-group--error")).toBe(true);
    });

    it("adds error classes to the field", () => {
      const { wrapper } = render({ errorMsg: "Oh no." });
      const formGroup = wrapper.find(".usa-select");

      expect(formGroup.hasClass("usa-input--error")).toBe(true);
    });
  });

  describe("when `smallLabel` is true", () => {
    it("sets the FormLabel small prop to true", () => {
      const { wrapper } = render({ smallLabel: true });
      const label = wrapper.find("FormLabel");

      expect(label.prop("small")).toBe(true);
    });
  });

  describe("when change event is triggered", () => {
    it("calls onChange", () => {
      const { props, wrapper } = render();

      wrapper.find(".usa-select").simulate("change");

      expect(props.onChange).toHaveBeenCalledTimes(1);
    });
  });

  describe("when `labelClassName` is set", () => {
    it("overrides the FormLabel .text-bold class", () => {
      const { wrapper } = render({ labelClassName: "text-normal" });
      const label = wrapper.find("FormLabel");

      expect(label.prop("labelClassName")).toBe("text-normal");
    });
  });

  describe("when formGroupClassName prop is set", () => {
    it("includes the formGroupClassName on the containing element", () => {
      const { wrapper } = render({ formGroupClassName: "custom-input-class" });

      expect(wrapper.hasClass("custom-input-class")).toBe(true);
    });
  });

  describe("when selectClassName prop is set", () => {
    it("includes the formGroupClassName on the containing element", () => {
      const { wrapper } = render({ selectClassName: "custom-input-class" });

      expect(wrapper.find("select").hasClass("custom-input-class")).toBe(true);
    });
  });

  describe("when `hideEmptyChoice` is not set", () => {
    it("displays empty choice as first option by default", () => {
      const { wrapper } = render();

      expect(wrapper.find("option")).toHaveLength(3);
      expect(wrapper.find("option").first().prop("value")).toEqual("");
    });
  });

  describe("when `hideEmptyChoice` is false", () => {
    it("displays empty choice as first option", () => {
      const { wrapper } = render({ hideEmptyChoice: false });

      expect(wrapper.find("option")).toHaveLength(3);
      expect(wrapper.find("option").first().prop("value")).toEqual("");
    });
  });

  describe("when `hideEmptyChoice` is true", () => {
    it("hides empty choice as first option", () => {
      const { wrapper } = render({ hideEmptyChoice: true });

      expect(wrapper.find("option")).toHaveLength(2);
      expect(wrapper.find("option").first().prop("value")).toEqual("a");
    });
  });

  describe("when `autocomplete` is true", () => {
    it("renders the list of options as combo-box", () => {
      const { wrapper } = render({ autocomplete: true });

      expect(wrapper.exists(".usa-combo-box")).toBe(true);
      expect(wrapper.find(".usa-combo-box")).toMatchSnapshot();
    });
  });
});
