import InputNumber from "../../src/components/InputNumber";
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

  describe("when valueType is not set", () => {
    const { props, wrapper } = render();

    it("allows empty fields", () => {
      const newValue = "";

      wrapper.simulate("change", {
        target: {
          value: newValue,
        },
      });

      expect(props.onChange).toHaveBeenCalledWith(
        expect.objectContaining({ target: { value: newValue } })
      );
    });

    it("allows comma-delimited numbers", () => {
      const newValue = "1,234";

      wrapper.simulate("change", {
        target: {
          value: newValue,
        },
      });

      expect(props.onChange).toHaveBeenCalledWith(
        expect.objectContaining({ target: { value: newValue } })
      );
    });

    it("allows numbers starting with a hyphen (negative numbers)", () => {
      const newValue = "-";

      wrapper.simulate("change", {
        target: {
          value: newValue,
        },
      });

      expect(props.onChange).toHaveBeenCalledWith(
        expect.objectContaining({ target: { value: newValue } })
      );
    });

    it("allows entering a decimal", () => {
      const newValue = "12.3";

      wrapper.simulate("change", {
        target: {
          value: newValue,
        },
      });

      expect(props.onChange).toHaveBeenCalledWith(
        expect.objectContaining({ target: { value: newValue } })
      );
    });

    it("prevents hyphen-delimited numbers", () => {
      const newValue = "123-123-123";

      wrapper.simulate("change", {
        stopPropagation: jest.fn(),
        target: {
          value: newValue,
        },
      });

      expect(props.onChange).not.toHaveBeenCalled();
    });

    it("prevents letters", () => {
      const newValue = "123a";

      wrapper.simulate("change", {
        stopPropagation: jest.fn(),
        target: {
          value: newValue,
        },
      });

      expect(props.onChange).not.toHaveBeenCalled();
    });
  });

  describe("when valueType is 'integer'", () => {
    const { props, wrapper } = render({ valueType: "integer" });

    it("allows empty fields", () => {
      const newValue = "";

      wrapper.simulate("change", {
        target: {
          value: newValue,
        },
      });

      expect(props.onChange).toHaveBeenCalledWith(
        expect.objectContaining({ target: { value: newValue } })
      );
    });

    it("allows comma-delimited numbers", () => {
      const newValue = "1,234";

      wrapper.simulate("change", {
        target: {
          value: newValue,
        },
      });

      expect(props.onChange).toHaveBeenCalledWith(
        expect.objectContaining({ target: { value: newValue } })
      );
    });

    it("allows numbers starting with a hyphen (negative numbers)", () => {
      const newValue = "-";

      wrapper.simulate("change", {
        target: {
          value: newValue,
        },
      });

      expect(props.onChange).toHaveBeenCalledWith(
        expect.objectContaining({ target: { value: newValue } })
      );
    });

    it("prevents entering a decimal", () => {
      const newValue = "12.3";

      wrapper.simulate("change", {
        stopPropagation: jest.fn(),
        target: {
          value: newValue,
        },
      });

      expect(props.onChange).not.toHaveBeenCalled();
    });

    it("prevents hyphen-delimited numbers", () => {
      const newValue = "123-123-123";

      wrapper.simulate("change", {
        stopPropagation: jest.fn(),
        target: {
          value: newValue,
        },
      });

      expect(props.onChange).not.toHaveBeenCalled();
    });

    it("prevents letters", () => {
      const newValue = "123a";

      wrapper.simulate("change", {
        stopPropagation: jest.fn(),
        target: {
          value: newValue,
        },
      });

      expect(props.onChange).not.toHaveBeenCalled();
    });
  });
});
