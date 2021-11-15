import InputNumber, {
  isAllowedValue,
} from "../../src/components/core/InputNumber";
import { render, screen } from "@testing-library/react";
import React from "react";
import userEvent from "@testing-library/user-event";

function setup(customProps = {}) {
  const props = {
    label: "Field Label",
    name: "field-name",
    onChange: jest.fn(),
    ...customProps,
  };

  const InputNumberWithState = (props) => {
    const [value, setValue] = React.useState(props.value ?? "");

    return (
      <InputNumber
        {...props}
        value={value}
        onChange={(event) => {
          setValue(event.target.value);
          props.onChange(event);
        }}
      />
    );
  };

  return render(<InputNumberWithState {...props} />);
}

describe("InputNumber", () => {
  it("renders input field", () => {
    const props = { label: "Foo", hint: "Bar", value: "123" };
    setup(props);

    const input = screen.getByRole("textbox", {
      name: `${props.label} ${props.hint}`,
      exact: false,
    });

    expect(input).toBeInTheDocument();
    expect(input).toHaveValue(props.value);
  });

  it("is always a text input", () => {
    setup({
      // This should be overridden with "text":
      type: "number",
    });

    expect(screen.getByRole("textbox")).toHaveAttribute("type", "text");
  });

  it("defaults inputMode to decimal when valueType is not set", () => {
    setup();

    expect(screen.getByRole("textbox")).toHaveAttribute("inputmode", "decimal");
  });

  it("defaults inputMode to numeric when valueType is integer", () => {
    setup({ valueType: "integer" });

    expect(screen.getByRole("textbox")).toHaveAttribute("inputmode", "numeric");
  });

  it("overrides the default inputMode prop when set", () => {
    setup({ valueType: "integer", inputMode: "decimal" });

    expect(screen.getByRole("textbox")).toHaveAttribute("inputmode", "decimal");
  });

  it("supports entering only integers when valueType is integer", () => {
    const onChange = jest.fn();
    setup({ valueType: "integer", onChange });
    const input = screen.getByRole("textbox");

    // No decimal point allowed
    userEvent.type(input, "1.");
    expect(input).toHaveValue("1");
  });

  it("supports entering decimals when valueType is float", () => {
    const onChange = jest.fn();
    setup({ valueType: "float", onChange });
    const input = screen.getByRole("textbox");

    userEvent.clear(input);
    userEvent.type(input, "1.");
    expect(input).toHaveValue("1.");
  });

  it("does not call onChange when value is not a number", () => {
    const onChange = jest.fn();
    setup({ valueType: "integer", onChange });

    const value = "a";
    userEvent.type(screen.getByRole("textbox"), value);

    expect(onChange).not.toHaveBeenCalled();
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
      expect(isAllowedValue("12.", allowDecimals, allowNegative)).toBe(true);
      expect(isAllowedValue("12.3", allowDecimals, allowNegative)).toBe(true);
    });

    it("prevents hyphen-delimited numbers", () => {
      const isAllowed = isAllowedValue(
        "123-123-123",
        allowDecimals,
        allowNegative
      );
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
      const isAllowed = isAllowedValue(
        "123-123-123",
        allowDecimals,
        allowNegative
      );
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
