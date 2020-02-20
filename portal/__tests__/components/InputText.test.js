import { mount, shallow } from "enzyme";
import InputText from "../../src/components/InputText";
import React from "react";

function render(customProps = {}, mountComponent = false) {
  const props = Object.assign(
    {
      label: "Field Label",
      name: "field-name",
      onChange: jest.fn()
    },
    customProps
  );

  const component = <InputText {...props} />;

  return {
    props,
    wrapper: mountComponent ? mount(component) : shallow(component)
  };
}

describe("InputText", () => {
  it("defaults to a text input", () => {
    const { wrapper } = render();
    const field = wrapper.find(".usa-input");

    expect(field.is("input")).toBe(true);
    expect(field.prop("type")).toBe("text");
  });

  it("sets the input's name", () => {
    const name = "foo";
    const { wrapper } = render({ name });
    const field = wrapper.find(".usa-input");

    expect(field.prop("name")).toBe(name);
  });

  it("sets the input's value", () => {
    const value = "Yay";
    const { wrapper } = render({ value });
    const field = wrapper.find(".usa-input");

    expect(field.prop("value")).toBe(value);
  });

  it("generates a unique id", () => {
    const { wrapper: wrapper1 } = render({ name: "one" });
    const { wrapper: wrapper2 } = render({ name: "two" });

    const input1 = wrapper1.find(".usa-input");
    const label1 = wrapper1.find("FormLabel");
    const input2 = wrapper2.find(".usa-input");

    const idRegex = new RegExp("InputText[0-9]+");

    expect(input1.prop("id")).toMatch(idRegex);
    expect(input1.prop("id")).not.toBe(input2.prop("id"));
    expect(label1.prop("inputId")).toBe(input1.prop("id"));
  });

  it("renders a label component", () => {
    const { props, wrapper } = render();
    const label = wrapper.find("FormLabel");

    expect(label.prop("children")).toBe(props.label);
  });

  describe("when type prop is set to password", () => {
    it("sets input type to password", () => {
      const { wrapper } = render({ type: "password" });
      const field = wrapper.find(".usa-input");

      expect(field.prop("type")).toBe("password");
    });
  });

  describe("when formGroupClassName prop is set", () => {
    it("includes the formGroupClassName on the containing element", () => {
      const { wrapper } = render({ formGroupClassName: "custom-input-class" });

      expect(wrapper.hasClass("custom-input-class")).toBe(true);
    });
  });

  describe("when hint prop is set", () => {
    it("passes the hint to FormLabel", () => {
      const { props, wrapper } = render({ hint: "123" });
      const label = wrapper.find("FormLabel");

      expect(label.prop("hint")).toBe(props.hint);
    });
  });

  describe("when inputClassName prop is set", () => {
    it("includes the inputClassName on the input field", () => {
      const { wrapper } = render({ inputClassName: "custom-input-class" });
      const input = wrapper.find("input");

      expect(input.hasClass("custom-input-class")).toBe(true);
    });
  });

  describe("when inputMode prop is set", () => {
    it("includes the inputMode on the input field", () => {
      const { wrapper } = render({ inputMode: "decimal" });
      const input = wrapper.find("input");

      expect(input.prop("inputMode")).toBe("decimal");
    });
  });

  describe("when inputRef prop is set", () => {
    it("sets the ref on the input field", () => {
      const ref = React.createRef();
      // We need to mount this component so we can access its ref
      const mountComponent = true;
      const { props } = render({ inputRef: ref, value: "abc" }, mountComponent);

      expect(ref.current.value).toBe(props.value);
    });
  });

  describe("when optionalText prop is set", () => {
    it("passes the optionalText to FormLabel", () => {
      const { props, wrapper } = render({ optionalText: "(optional)" });
      const label = wrapper.find("FormLabel");

      expect(label.prop("optionalText")).toBe(props.optionalText);
    });
  });

  describe("when width prop is set", () => {
    it("adds width classes to input", () => {
      const mediumData = render({ width: "medium" });
      const mediumField = mediumData.wrapper.find(".usa-input");
      const smallData = render({ width: "small" });
      const smallField = smallData.wrapper.find(".usa-input");

      expect(mediumField.hasClass("usa-input--medium")).toBe(true);
      expect(smallField.hasClass("usa-input--small")).toBe(true);
    });
  });

  describe("when errorMsg is set", () => {
    it("passes errorMsg to FormLabel", () => {
      const { props, wrapper } = render({ errorMsg: "Oh no." });

      expect(wrapper.find("FormLabel").prop("errorMsg")).toBe(props.errorMsg);
    });

    it("adds error classes to the form group and input field", () => {
      const { wrapper } = render({ errorMsg: "Oh no." });
      const formGroup = wrapper.find(".usa-form-group");
      const field = wrapper.find(".usa-input");

      expect(formGroup.hasClass("usa-form-group--error")).toBe(true);
      expect(field.hasClass("usa-input--error")).toBe(true);
    });
  });

  describe("when change event is triggered", () => {
    it("calls onChange", () => {
      const { props, wrapper } = render({
        onChange: jest.fn()
      });

      wrapper.find(".usa-input").simulate("change");

      expect(props.onChange).toHaveBeenCalledTimes(1);
    });
  });
});
