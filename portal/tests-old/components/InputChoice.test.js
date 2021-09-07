import InputChoice from "../../src/components/InputChoice";
import React from "react";
import { shallow } from "enzyme";

function render(customProps = {}) {
  const props = Object.assign(
    {
      label: "Field Label",
      name: "field-name",
      value: "field-value",
      disabled: false,
    },
    customProps
  );

  const component = <InputChoice {...props} />;

  return {
    props,
    wrapper: shallow(component),
  };
}

describe("InputChoice", () => {
  it("sets the input's name", () => {
    const name = "foo";
    const { wrapper } = render({ name });
    const field = wrapper.find("input");

    expect(field.prop("name")).toBe(name);
  });

  it("sets the input's value", () => {
    const value = "Yay";
    const { wrapper } = render({ value });
    const field = wrapper.find("input");

    expect(field.prop("value")).toBe(value);
  });

  it("sets the input's disabled attribute", () => {
    const disabled = true;
    const { wrapper } = render({ disabled });
    const field = wrapper.find("input");

    expect(field.prop("disabled")).toBe(disabled);
  });

  it("sets the className", () => {
    const { wrapper } = render({ type: "checkbox", className: "foo" });

    expect(wrapper.hasClass("usa-checkbox")).toBe(true);
    expect(wrapper.hasClass("foo")).toBe(true);
  });

  it("generates a unique id if none is provided", () => {
    const { wrapper: wrapper1 } = render({ name: "one" });
    const { wrapper: wrapper2 } = render({ name: "two" });
    const { wrapper: wrapper3 } = render({ name: "three", id: "three" });

    const input1 = wrapper1.find("input");
    const label1 = wrapper1.find("label");
    const input2 = wrapper2.find("input");
    const input3 = wrapper3.find("input");

    expect(input1.prop("id")).not.toBe(input2.prop("id"));
    expect(label1.prop("htmlFor")).toBe(input1.prop("id"));
    expect(input3.prop("id")).toEqual("three");
  });

  it("renders a label", () => {
    const { props, wrapper } = render();
    const label = wrapper.find("label");

    expect(label.text()).toMatch(props.label);
  });

  describe("when hint prop is set", () => {
    it("renders the hint inside the label", () => {
      const { props, wrapper } = render({ hint: "Hello world" });
      const hint = wrapper.find("label .usa-hint");

      expect(hint.text()).toMatch(props.hint);
    });
  });

  describe("when ariaControls prop is set", () => {
    it("renders an aria-controls attribute", () => {
      const { wrapper } = render({ ariaControls: "my-element" });
      const input = wrapper.find("input");

      expect(input.prop("aria-controls")).toBe("my-element");
    });
  });

  describe("when the type prop isn't set", () => {
    it("defaults to a checkbox", () => {
      const { wrapper } = render();
      const field = wrapper.find("input");

      expect(field.prop("type")).toBe("checkbox");
    });

    it("uses checkbox class names", () => {
      const { wrapper } = render();

      expect(wrapper.find(".usa-checkbox")).toHaveLength(1);
      expect(wrapper.find(".usa-checkbox__input")).toHaveLength(1);
      expect(wrapper.find(".usa-checkbox__label")).toHaveLength(1);
    });
  });

  describe("when type prop is set to radio", () => {
    it("sets input type to radio", () => {
      const { wrapper } = render({ type: "radio" });
      const field = wrapper.find("input");

      expect(field.prop("type")).toBe("radio");
    });

    it("uses radio class names", () => {
      const { wrapper } = render({ type: "radio" });

      expect(wrapper.find(".usa-radio")).toHaveLength(1);
      expect(wrapper.find(".usa-radio__input")).toHaveLength(1);
      expect(wrapper.find(".usa-radio__label")).toHaveLength(1);
    });
  });

  describe("when change event is triggered", () => {
    it("calls onChange", () => {
      const { props, wrapper } = render({
        onChange: jest.fn(),
      });

      wrapper.find("input").simulate("change");

      expect(props.onChange).toHaveBeenCalledTimes(1);
    });
  });
});
