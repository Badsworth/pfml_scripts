import Mask, { maskValue } from "../../src/components/Mask";
import { mount, shallow } from "enzyme";
import React from "react";

const masks = ["currency", "fein", "ssn", "zip"];

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

  it("renders mask", () => {
    const data = render({
      mask: "ssn",
    });

    expect(data.wrapper).toMatchSnapshot();
  });

  it("adds `inputMode='number'` to the child element", () => {
    const { wrapper } = render({ mask: "ssn" }, { value: "123456789" });
    const input = wrapper.find("input");

    expect(input.prop("inputMode")).toBe("numeric");
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

    input.simulate("blur", { target: { value: "12345678" } });

    expect(inputOnChange).toHaveBeenCalledTimes(1);
  });

  it("masking is triggered by a blur event", () => {
    const inputOnChange = jest.fn();
    const wrapper = render(
      { mask: "ssn" },
      { value: "123456789", onChange: inputOnChange }
    ).wrapper;

    const input = wrapper.find("input");

    input.simulate("blur", { target: { value: "123456789" } });

    expect(inputOnChange.mock.calls[0][0].target.value).toBe("123-45-6789");
  });

  it("masking is triggered by keypress on Enter key", () => {
    const inputOnChange = jest.fn();
    const wrapper = render(
      { mask: "ssn" },
      { value: "123456789", onChange: inputOnChange }
    ).wrapper;

    const input = wrapper.find("input");

    input.simulate("keyDown", { key: "Enter", target: { value: "123456789" } });

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
  });

  describe("currency", () => {
    it("inserts commas", () => {
      const originalValue = "12345.557";
      const output = maskValue(originalValue, "currency");

      expect(output).toBe("12,345.56");
    });

    it("rounds decimals", () => {
      const originalValue = "12345.557";
      const output = maskValue(originalValue, "currency");

      expect(output).toBe("12,345.56");
    });

    it("allows only numbers and decimals", () => {
      const originalValue = "abc12345.def557ghi";
      const output = maskValue(originalValue, "currency");

      expect(output).toBe("12,345.56");
    });
  });
});
