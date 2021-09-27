import { render, screen } from "@testing-library/react";
import InputText from "../../src/components/InputText";
import React from "react";
import userEvent from "@testing-library/user-event";

function setup(customProps = {}) {
  const props = Object.assign(
    {
      label: "Field Label",
      name: "field-name",
      onChange: jest.fn(),
    },
    customProps
  );

  return render(<InputText {...props} />);
}

describe("InputText", () => {
  it("defaults to a text input", () => {
    setup();

    expect(screen.getByRole("textbox")).toHaveAttribute("type", "text");
  });

  it("sets the input's name and value", () => {
    const name = "foo";
    const value = "Yay";
    setup({ name, value });

    const field = screen.getByRole("textbox");

    expect(field).toHaveAttribute("name", name);
    expect(field).toHaveValue(value);
  });

  it("associates label and hint text to the field", () => {
    const label = "Field Label";
    const hint = "Field Hint";
    setup({ label, hint });

    expect(
      screen.getByRole("textbox", {
        name: `${label} ${hint}`,
      })
    ).toBeInTheDocument();
  });

  it("supports inline error message and styling", () => {
    const { container } = setup({ errorMsg: "Oh no" });
    const field = screen.getByRole("textbox", {
      name: /Oh no/i,
    });

    expect(field).toHaveClass("usa-input--error");
    expect(container.firstChild).toHaveClass("usa-form-group--error");
  });

  it("supports setting the Optional text in the label", () => {
    setup({ optionalText: "Optional" });

    expect(
      screen.getByRole("textbox", { name: /optional/i })
    ).toBeInTheDocument();
  });

  it("supports providing an example", () => {
    const example = "For example: 1/2/3";
    setup({ example });

    expect(screen.getByText(example)).toBeInTheDocument();
  });

  it("sets a unique id by default", () => {
    setup({ name: "one" });
    setup({ name: "two" });

    const idRegex = /InputText[0-9]+/;
    const [fieldOne, fieldTwo] = screen.getAllByRole("textbox");

    expect(fieldOne.id).toMatch(idRegex);
    expect(fieldOne.id).not.toBe(fieldTwo.id);
  });

  it("supports a custom ID", () => {
    const label = "Unique ID field";
    setup({ inputId: "my-unique-id", label });

    const field = screen.getByRole("textbox", { name: label });

    expect(field.id).toBe("my-unique-id");
  });

  it("supports autocomplete attribute", () => {
    setup({ autoComplete: "address-line1" });

    expect(screen.getByRole("textbox")).toHaveAttribute(
      "autocomplete",
      "address-line1"
    );
  });

  it("prevents usage of HTML number type", () => {
    jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
    setup({ type: "number" });

    const field = screen.getByRole("textbox");

    expect(field.type).toBe("text");
    expect(field.inputMode).toBe("numeric");
  });

  it("supports password input type", () => {
    setup({ type: "password", label: "Password field" });
    // Password inputs don't have an implicit role
    // https://github.com/testing-library/dom-testing-library/issues/567
    const field = screen.getByLabelText("Password field");

    expect(field.type).toBe("password");
  });

  it("supports usage of inputMode", () => {
    setup({ inputMode: "decimal" });
    const input = screen.getByRole("textbox");

    expect(input.inputMode).toBe("decimal");
  });

  it("sets the data-value-type attribute on the input when valueType prop is set", () => {
    setup({ valueType: "integer" });
    const input = screen.getByRole("textbox");

    expect(input).toHaveAttribute("data-value-type", "integer");
  });

  it("supports getting a ref to the input", () => {
    const ref = React.createRef();
    setup({ inputRef: ref });

    expect(ref.current).toBe(screen.getByRole("textbox"));
  });

  it("supports maxLength", () => {
    setup({ maxLength: "4" });
    const input = screen.getByRole("textbox");

    expect(input).toHaveAttribute("maxlength", "4");
  });

  it("supports a custom class on the containing element", () => {
    const { container } = setup({ formGroupClassName: "custom-input-class" });

    expect(container.firstChild).toHaveClass("custom-input-class");
  });

  it("supports various width classes on the input", () => {
    setup({ width: "medium" });
    setup({ width: "small" });

    const [mediumField, smallField] = screen.getAllByRole("textbox");

    expect(mediumField).toHaveClass("usa-input--medium");
    expect(smallField).toHaveClass("usa-input--small");
  });

  it("supports a custom class on the label", () => {
    setup({ labelClassName: "text-normal", label: "Field label" });
    const label = screen.getByText("Field label");

    expect(label).toHaveClass("text-normal");
  });

  it("supports the small label variation", () => {
    setup({ smallLabel: true, label: "Field label" });
    const label = screen.getByText("Field label");

    expect(label).toHaveClass("font-heading-xs");
  });

  it("supports onChange and onBlur events", () => {
    const onChange = jest.fn();
    const onBlur = jest.fn();
    setup({
      onBlur,
      onChange,
    });
    const field = screen.getByRole("textbox");

    userEvent.type(field, "123");
    expect(onChange).toHaveBeenCalledTimes(3);

    field.blur();
    expect(onBlur).toHaveBeenCalledTimes(1);
  });

  it("supports masking behavior", () => {
    setup({ mask: "currency", value: "1234" });

    expect(screen.getByRole("textbox")).toHaveAttribute("inputmode", "decimal");
  });

  it("supports viewing obfuscated PII and changing the PII", () => {
    const onChange = jest.fn();
    const onBlur = jest.fn();
    const initialValue = "***-123";

    setup({
      pii: true,
      onBlur,
      onChange,
      value: initialValue,
    });

    const field = screen.getByRole("textbox");

    field.focus();
    expect(onChange).toHaveBeenCalledTimes(1);
    field.blur();
    expect(onBlur).toHaveBeenCalledTimes(1);

    userEvent.type(field, "000");
    expect(onChange).toHaveBeenCalledTimes(4);
  });
});
