import Mask, { maskValue } from "../../src/components/Mask";
import { mount, shallow } from "enzyme";
import React from "react";
import { createInputElement } from "../test-utils";

const masks = ["currency", "fein", "hours", "phone", "ssn", "zip"];

function render(customProps = {}, inputProps = {}, mountComponent = false) {
  const component = (
    <Mask {...customProps}>
      <input name="foo" type="text" {...inputProps} />
    </Mask>
  );

  return {
    props: customProps,
    wrapper: mountComponent ? mount(component) : shallow(component),
  };
}

describe("Mask", () => {
  masks.forEach((mask) => {
    describe(`${mask} fallbacks`, () => {
      it("renders a blank field when value is empty", () => {
        const { wrapper } = render({ mask }, { value: "" });
        const input = wrapper.find("input");

        expect(input.prop("value")).toBe("");
      });
    });
  });

  it("renders ssn mask", () => {
    const data = render({
      mask: "ssn",
    });

    expect(data.wrapper).toMatchSnapshot();
  });

  it("adds `type='text'` to the ssn masked element", () => {
    const { wrapper } = render({ mask: "ssn" }, { value: "123456789" });
    const input = wrapper.find("input");

    expect(input.prop("type")).toBe("text");
  });

  it("adds `type='tel'` to the phone masked element", () => {
    const { wrapper } = render({ mask: "phone" }, { value: "123456789" });
    const input = wrapper.find("input");

    expect(input.prop("type")).toBe("tel");
  });

  it("adds `inputMode='number'` to the child element", () => {
    const { wrapper } = render({ mask: "ssn" }, { value: "123456789" });
    const input = wrapper.find("input");

    expect(input.prop("inputMode")).toBe("numeric");
  });

  it("adds `inputMode='decimal'` to the child element when mask is currency", () => {
    const { wrapper } = render({ mask: "currency" }, { value: "123456789" });
    const input = wrapper.find("input");

    expect(input.prop("inputMode")).toBe("decimal");
  });

  it("applies icon prefix to the child element when mask is currency", () => {
    const { wrapper } = render({ mask: "currency" }, { value: "123456789" });
    const input = wrapper.find("div").last();

    expect(input.prop("className")).toEqual("usa-input-prefix");
    expect(input).toMatchSnapshot();
  });

  it("adds `inputMode='decimal'` to the child element when mask is hours", () => {
    const { wrapper } = render({ mask: "hours" }, { value: "123456789" });
    const input = wrapper.find("input");

    expect(input.prop("inputMode")).toBe("decimal");
  });

  it("does not mask if an invalid mask value is passed in", () => {
    //   Suppress the console.error that otherwise gets logged in the test.
    jest.spyOn(console, "error").mockImplementation(jest.fn());
    const { wrapper } = render({ mask: "foo" }, { value: "12345" });
    const input = wrapper.find("input");

    expect(input.prop("value")).toBe("12345");
  });

  it("calls onChange on the InputText on a blur event", () => {
    const inputOnChange = jest.fn();
    const wrapper = render(
      { mask: "ssn" },
      { value: "12345678", onChange: inputOnChange }
    ).wrapper;

    const input = wrapper.find("input");

    input.simulate("blur", {
      target: createInputElement({ value: "12345678" }),
    });

    expect(inputOnChange).toHaveBeenCalledTimes(1);
  });

  it("masking is triggered by a blur event", () => {
    const inputOnChange = jest.fn();
    const wrapper = render(
      { mask: "ssn" },
      { value: "123456789", onChange: inputOnChange }
    ).wrapper;

    const input = wrapper.find("input");

    input.simulate("blur", {
      target: createInputElement({ value: "123456789" }),
    });

    expect(inputOnChange.mock.calls[0][0].target.value).toBe("123-45-6789");
  });

  it("masking is triggered by keypress on Enter key", () => {
    const inputOnChange = jest.fn();
    const wrapper = render(
      { mask: "ssn" },
      { value: "123456789", onChange: inputOnChange }
    ).wrapper;

    const input = wrapper.find("input");

    input.simulate("keyDown", {
      key: "Enter",
      target: createInputElement({ value: "123456789" }),
    });

    expect(inputOnChange.mock.calls[0][0].target.value).toBe("123-45-6789");
  });

  it("masking is not triggered by a change event", () => {
    const inputOnChange = jest.fn();
    const wrapper = render(
      { mask: "ssn" },
      { value: "12345678", onChange: inputOnChange }
    ).wrapper;

    const input = wrapper.find("input");

    input.simulate("change", { target: { value: "123456789" } });

    expect(inputOnChange.mock.calls[0][0].target.value).toBe("123456789");
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
