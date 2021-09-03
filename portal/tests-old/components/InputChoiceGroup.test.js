import InputChoiceGroup from "../../src/components/InputChoiceGroup";
import React from "react";
import { shallow } from "enzyme";

function render(customProps = {}) {
  const props = Object.assign(
    {
      choices: [
        {
          label: "Choice A",
          value: "a",
        },
        {
          label: "Choice B",
          value: "b",
        },
      ],
      label: "Field label",
      name: "field-name",
    },
    customProps
  );

  const component = <InputChoiceGroup {...props} />;

  return {
    props,
    wrapper: shallow(component),
  };
}

describe("InputChoiceGroup", () => {
  it("groups everything within a Fieldset", () => {
    const { wrapper } = render();

    expect(wrapper.is("Fieldset")).toBe(true);
  });

  it("renders a legend", () => {
    const { wrapper } = render({
      errorMsg: "Error message",
      hint: "Hint text",
      optionalText: "Optional",
    });

    expect(wrapper.find("FormLabel")).toMatchSnapshot();
  });

  it("renders an InputChoice for each object in choices", () => {
    const { wrapper } = render();

    expect(wrapper.find("InputChoice")).toMatchSnapshot();
  });

  it("sets the name on each InputChoice", () => {
    const name = "foo";
    const { wrapper } = render({ name });
    const choices = wrapper.find("InputChoice");

    // make sure our usage of .first() and .last() are doing what we expect
    expect(choices.length > 1).toBe(true);

    expect(choices.first().prop("name")).toBe(name);
    expect(choices.last().prop("name")).toBe(name);
  });

  describe("when the type prop isn't set", () => {
    it("sets the InputChoice type to checkbox", () => {
      const { wrapper } = render();
      const choices = wrapper.find("InputChoice");

      expect(choices.first().prop("type")).toBe("checkbox");
    });
  });

  describe("when type prop is set to radio", () => {
    it("sets the InputChoice type to radio", () => {
      const { props, wrapper } = render({ type: "radio" });
      const choices = wrapper.find("InputChoice");

      expect(choices.first().prop("type")).toBe(props.type);
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
  });

  describe("when change event is triggered", () => {
    it("calls onChange", () => {
      const { props, wrapper } = render({
        onChange: jest.fn(),
      });

      wrapper.find("InputChoice").first().simulate("change");

      expect(props.onChange).toHaveBeenCalledTimes(1);
    });
  });
});
