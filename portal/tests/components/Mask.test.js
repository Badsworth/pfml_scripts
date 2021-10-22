import Mask, { maskValue } from "../../src/components/Mask";
import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import userEvent from "@testing-library/user-event";

const masks = ["currency", "fein", "hours", "phone", "ssn", "zip"];

const renderMask = (customProps = {}, inputProps = {}) => {
  const component = (
    <Mask {...customProps}>
      <input name="foo" type="text" {...inputProps} />
    </Mask>
  );

  return render(component);
};

describe("Mask", () => {
  masks.forEach((mask) => {
    describe(`${mask} fallbacks`, () => {
      it("renders a blank field when value is empty", () => {
        renderMask({ mask }, { value: "", onChange: jest.fn() });
        const input = screen.getByRole("textbox");

        expect(input).toHaveValue("");
      });
    });
  });

  it("renders ssn mask", () => {
    const { container } = renderMask({
      mask: "ssn",
    });

    expect(container.firstChild).toMatchSnapshot();
  });

  it("adds `type='text'` to the ssn masked element", () => {
    renderMask({ mask: "ssn" }, { value: "123456789", onChange: jest.fn() });
    const input = screen.getByRole("textbox");

    expect(input).toHaveAttribute("type", "text");
  });

  it("adds `type='tel'` to the phone masked element", () => {
    renderMask({ mask: "phone" }, { value: "123456789", onChange: jest.fn() });
    const input = screen.getByRole("textbox");

    expect(input).toHaveAttribute("type", "tel");
  });

  it("adds `inputMode='number'` to the child element", () => {
    renderMask({ mask: "ssn" }, { value: "123456789", onChange: jest.fn() });
    const input = screen.getByRole("textbox");

    expect(input).toHaveAttribute("inputMode", "numeric");
  });

  it("adds `inputMode='decimal'` to the child element when mask is currency", () => {
    renderMask(
      { mask: "currency" },
      { value: "123456789", onChange: jest.fn() }
    );
    const input = screen.getByRole("textbox");

    expect(input).toHaveAttribute("inputMode", "decimal");
  });

  it("applies icon prefix to the child element when mask is currency", () => {
    const { container } = renderMask(
      { mask: "currency" },
      { value: "123456789", onChange: jest.fn() }
    );
    expect(container.firstChild).toMatchSnapshot();
  });

  it("adds `inputMode='decimal'` to the child element when mask is hours", () => {
    renderMask({ mask: "hours" }, { value: "123456789", onChange: jest.fn() });
    const input = screen.getByRole("textbox");

    expect(input).toHaveAttribute("inputMode", "decimal");
  });

  it("does not mask if an invalid mask value is passed in", () => {
    //   Suppress the console.error that otherwise gets logged in the test.
    jest.spyOn(console, "error").mockImplementation(jest.fn());
    renderMask({ mask: "foo" }, { value: "12345", onChange: jest.fn() });
    const input = screen.getByRole("textbox");
    expect(input).toHaveValue("12345");
  });

  it("calls onChange on the InputText on a blur event", () => {
    const inputOnChange = jest.fn();
    renderMask({ mask: "ssn" }, { value: "12345678", onChange: inputOnChange });

    const input = screen.getByRole("textbox");

    fireEvent.blur(input);

    expect(inputOnChange).toHaveBeenCalledTimes(1);
  });

  it("masking is triggered by a blur event", () => {
    const inputOnChange = jest.fn();
    renderMask(
      { mask: "ssn" },
      { value: "123456789", onChange: inputOnChange }
    );

    const input = screen.getByRole("textbox");

    fireEvent.blur(input);

    expect(inputOnChange.mock.calls[0][0].target.value).toBe("123-45-6789");
  });

  it("masking is triggered by keypress on Enter key", () => {
    const inputOnChange = jest.fn();
    renderMask(
      { mask: "ssn" },
      { value: "123456789", onChange: inputOnChange }
    );

    const input = screen.getByRole("textbox");

    userEvent.type(input, "{enter}");

    expect(inputOnChange.mock.calls[0][0].target.value).toBe("123-45-6789");
  });

  it("masking is not triggered by a change event", () => {
    const MaskedInputWithState = ({ initialValue }) => {
      const [value, setValue] = React.useState(initialValue);
      const handleChange = ({ target: { value } }) => setValue(value);

      return (
        <Mask mask="ssn">
          <input name="foo" type="text" value={value} onChange={handleChange} />
        </Mask>
      );
    };

    render(<MaskedInputWithState initialValue="12345678" />);

    const input = screen.getByRole("textbox");
    userEvent.type(input, "9");

    expect(input).toHaveValue("123456789");
  });

  describe("maskValue", () => {
    it("returns original value if invalid mask is passed in", () => {
      const originalValue = "123456789";
      const output = maskValue(originalValue, "faker");

      expect(output).toBe(originalValue);
    });

    describe("SSN", () => {
      it("accepts empty values", () => {
        const originalValue = "";
        const output = maskValue(originalValue, "ssn");

        expect(output).toBe("");
      });

      it("accepts partial SSNs", () => {
        const originalValue = "123";
        const output = maskValue(originalValue, "ssn");

        expect(output).toBe("123");
      });

      it("accepts partial (4 digit) SSNs", () => {
        const originalValue = "1234";
        const output = maskValue(originalValue, "ssn");

        expect(output).toBe("123-4");
      });

      it("accepts partial (6 digit) SSNs", () => {
        const originalValue = "123456";
        const output = maskValue(originalValue, "ssn");

        expect(output).toBe("123-45-6");
      });

      it("accepts full SSNs", () => {
        const originalValue = "123456789";
        const output = maskValue(originalValue, "ssn");

        expect(output).toBe("123-45-6789");
      });

      it("accepts an unexpectedly long value", () => {
        const originalValue = "1234567890";
        const output = maskValue(originalValue, "ssn");

        expect(output).toBe("123-45-67890");
      });

      it("accepts dashes in value", () => {
        const originalValue = "123-45-6789";
        const output = maskValue(originalValue, "ssn");

        expect(output).toBe("123-45-6789");
      });

      it("accepts spaces in value", () => {
        const originalValue = "123 45 6789";
        const output = maskValue(originalValue, "ssn");

        expect(output).toBe("123-45-6789");
      });

      it("accepts partially masked value", () => {
        const originalValue = "123-45-****";
        const output = maskValue(originalValue, "ssn");

        expect(output).toBe("123-45-****");
      });
    });
  });

  describe("FEIN", () => {
    it("accepts full FEINs", () => {
      const originalValue = "121234567";
      const output = maskValue(originalValue, "fein");

      expect(output).toBe("12-1234567");
    });

    it("accepts an unexpectedly long value", () => {
      const originalValue = "12123456789";
      const output = maskValue(originalValue, "fein");

      expect(output).toBe("12-123456789");
    });

    it("accepts spaces in value", () => {
      const originalValue = "12 1234567";
      const output = maskValue(originalValue, "fein");

      expect(output).toBe("12-1234567");
    });

    it("accepts dashes in value", () => {
      const originalValue = "12-1234567";
      const output = maskValue(originalValue, "fein");

      expect(output).toBe("12-1234567");
    });

    it("accepts partially masked value", () => {
      const originalValue = "**-***1234";
      const output = maskValue(originalValue, "fein");

      expect(output).toBe("**-***1234");
    });
  });

  describe("currency and hours", () => {
    it("inserts commas", () => {
      const originalValue = "12345.557";
      const outputCurrency = maskValue(originalValue, "currency");
      const outputHours = maskValue(originalValue, "hours");

      expect(outputCurrency).toBe("12,345.56");
      expect(outputHours).toBe("12,345.56");
    });

    it("rounds decimals", () => {
      const originalValue = "12345.557";
      const outputCurrency = maskValue(originalValue, "currency");
      const outputHours = maskValue(originalValue, "hours");

      expect(outputCurrency).toBe("12,345.56");
      expect(outputHours).toBe("12,345.56");
    });

    it("allows only numbers and decimals", () => {
      const originalValue = "abc12345.def557ghi";
      const outputCurrency = maskValue(originalValue, "currency");
      const outputHours = maskValue(originalValue, "hours");

      expect(outputCurrency).toBe("12,345.56");
      expect(outputHours).toBe("12,345.56");
    });
  });

  describe("phone", () => {
    it("inserts dashes", () => {
      const originalValue = "5551234567";
      const output = maskValue(originalValue, "phone");

      expect(output).toBe("555-123-4567");
    });

    it("accepts phone formatted with parenthesis", () => {
      const originalValue = "(555) 123-4567";
      const output = maskValue(originalValue, "phone");

      expect(output).toBe("555-123-4567");
    });

    it("accepts an unexpectedly long value", () => {
      const originalValue = "555123456790";
      const output = maskValue(originalValue, "phone");

      expect(output).toBe("555-123-456790");
    });

    it("accepts partially masked value", () => {
      const originalValue = "555-123-****";
      const output = maskValue(originalValue, "phone");

      expect(output).toBe("555-123-****");
    });
  });

  describe("zip", () => {
    it("accepts 5-digit ZIP code", () => {
      const originalValue = "12345";
      const output = maskValue(originalValue, "zip");

      expect(output).toBe("12345");
    });

    it("accepts 9-digit ZIP code", () => {
      const originalValue = "12345-6789";
      const output = maskValue(originalValue, "zip");

      expect(output).toBe("12345-6789");
    });

    it("accepts 9-digit ZIP code without dash", () => {
      const originalValue = "123456789";
      const output = maskValue(originalValue, "zip");

      expect(output).toBe("12345-6789");
    });

    it("accepts partially masked 9-digit ZIP code", () => {
      const originalValue = "12345-****";
      const output = maskValue(originalValue, "zip");

      expect(output).toBe("12345-****");
    });
  });
});
