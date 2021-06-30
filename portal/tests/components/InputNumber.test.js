import InputNumber, { isAllowedValue } from "../../src/components/InputNumber";

import React from "react";
import { shallow } from "enzyme";

function render(customProps = {}, mountComponent = false) {
  const props = Object.assign(
    {
      label: "Field Label",
      name: "field-name",
      onChange: jest.fn(),
    },
    customProps
  );

  const component = <InputNumber {...props} />;

  return {
    props,
    wrapper: shallow(component),
  };
}

describe("InputNumber", () => {
  it("passes props to InputText", () => {
    const { wrapper } = render({ label: "Foo", hint: "Bar", value: "123" });

    expect(wrapper.prop("label")).toBe("Foo");
    expect(wrapper.prop("hint")).toBe("Bar");
    expect(wrapper.prop("value")).toBe("123");
  });

  it("is always a text input", () => {
    const { wrapper } = render({
      // This should be overridden with "text":
      type: "number",
    });

    expect(wrapper.prop("type")).toBe("text");
  });

  it("defaults inputMode to decimal when valueType is not set", () => {
    const { wrapper } = render();

    expect(wrapper.prop("inputMode")).toBe("decimal");
  });

  it("defaults inputMode to numeric when valueType is integer", () => {
    const { wrapper } = render({ valueType: "integer" });

    expect(wrapper.prop("valueType")).toBe("integer");
    expect(wrapper.prop("inputMode")).toBe("numeric");
  });

  it("overrides the default inputMode prop when set", () => {
    const { wrapper } = render({ valueType: "integer", inputMode: "decimal" });

    expect(wrapper.prop("inputMode")).toBe("decimal");
  });

  describe("with an allowed value", () => {
    const { props, wrapper } = render({ valueType: "integer" });
    const value = "123"

    it("calls onChange", () => {
      wrapper.simulate("change", {
        target: { value },
      });

      expect(props.onChange).toHaveBeenCalledWith(
        expect.objectContaining({ target: { value } })
      );
    });
  });

  describe("with a disallowed value", () => {
    const { props, wrapper } = render({ valueType: "integer" });
    const value = "abc"

    it("does not call onChange", () => {
      wrapper.simulate("change", {
        stopPropagation: jest.fn(),
        target: { value },
      });

      expect(props.onChange).not.toHaveBeenCalled();
    });
  });
});


describe("isAllowedValue", () => {
  const allowDecimals = true;
  const allowNegative = true;

  describe("when decimals are allowed", () => {
    const allowDecimals = true;

    it("allows empty fields", () => {
      const isAllowed = isAllowedValue("", allowDecimals, allowNegative);
      expect(isAllowed).toBe(true);
    });

    it("allows comma-delimited numbers", () => {
      const isAllowed = isAllowedValue("1,234", allowDecimals, allowNegative);
      expect(isAllowed).toBe(true);
    });

    it("allows numbers starting with a hyphen (negative numbers)", () => {
      const isAllowed = isAllowedValue("-1", allowDecimals, allowNegative);
      expect(isAllowed).toBe(true);
    });

    it("allows entering a decimal", () => {
      const isAllowed = isAllowedValue("12.3", allowDecimals, allowNegative);
      expect(isAllowed).toBe(true);
    });

    it("prevents hyphen-delimited numbers", () => {
      const isAllowed = isAllowedValue("123-123-123", allowDecimals, allowNegative);
      expect(isAllowed).toBe(false);
    });

    it("prevents letters", () => {
      const isAllowed = isAllowedValue("123a", allowDecimals, allowNegative);
      expect(isAllowed).toBe(false);
    });
  });

  describe("when decimals are not allowed", () => {
    const allowDecimals = false;

    it("allows empty fields", () => {
      const isAllowed = isAllowedValue("", allowDecimals, allowNegative);
      expect(isAllowed).toBe(true);
    });

    it("allows comma-delimited numbers", () => {
      const isAllowed = isAllowedValue("1,234", allowDecimals, allowNegative);
      expect(isAllowed).toBe(true);
    });

    it("allows numbers starting with a hyphen (negative numbers)", () => {
      const isAllowed = isAllowedValue("-1", allowDecimals, allowNegative);
      expect(isAllowed).toBe(true);
    });

    it("prevents entering a decimal", () => {
      const isAllowed = isAllowedValue("12.3", allowDecimals, allowNegative);
      expect(isAllowed).toBe(false);
    });

    it("prevents hyphen-delimited numbers", () => {
      const isAllowed = isAllowedValue("123-123-123", allowDecimals, allowNegative);
      expect(isAllowed).toBe(false);
    });

    it("prevents letters", () => {
      const isAllowed = isAllowedValue("123a", allowDecimals, allowNegative);
      expect(isAllowed).toBe(false);
    });
  });

  describe("when negatives are allowed", () => {
    const allowNegative = true;

    it("allows numbers starting with a hyphen (negative numbers)", () => {
      const isAllowed = isAllowedValue("-1", allowDecimals, allowNegative);
      expect(isAllowed).toBe(true);
    });
  });

  describe("when negatives are not allowed", () => {
    const allowNegative = false;

    it("prevents numbers starting with a hyphen (negative numbers)", () => {
      const isAllowed = isAllowedValue("-1", allowDecimals, allowNegative);
      expect(isAllowed).toBe(false);
    });
  });
});
