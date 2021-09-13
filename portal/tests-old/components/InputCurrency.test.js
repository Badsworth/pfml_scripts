import { createInputElement, testHook } from "../test-utils";
import { mount, shallow } from "enzyme";
import InputCurrency from "../../src/components/InputCurrency";
import React from "react";
import useHandleInputChange from "../../src/hooks/useHandleInputChange";

function render(customProps = {}, mountComponent = false) {
  const props = Object.assign(
    {
      label: "Field Label",
      name: "field-name",
      onChange: jest.fn(),
    },
    customProps
  );

  const component = <InputCurrency {...props} />;

  return {
    props,
    wrapper: mountComponent ? mount(component) : shallow(component),
  };
}

describe("InputCurrency", () => {
  it("passes props to InputNumber", () => {
    const { wrapper } = render({
      label: "Money",
      name: "money",
      hint: "More problems",
    });

    expect(wrapper.prop("label")).toBe("Money");
    expect(wrapper.prop("hint")).toBe("More problems");
    expect(wrapper.prop("name")).toBe("money");
  });

  const values = [
    [null, ""],
    [25000, "25,000"],
    [1000000.55, "1,000,000.55"],
    [-5050.25, "-5,050.25"],
  ];

  it("displays the components value as a masked string", () => {
    values.forEach(([value, expectedMask]) => {
      const { wrapper } = render({
        label: "Money",
        name: "money",
        value,
      });

      expect(wrapper.prop("value")).toBe(expectedMask);
    });
  });

  it("updates state with the number value when used with useHandleInputChange", () => {
    values.forEach(([expectedValue, maskedValue]) => {
      const updateFields = jest.fn();
      let onChange;
      testHook(() => {
        onChange = useHandleInputChange(updateFields);
      });
      const { wrapper } = render(
        {
          label: "Money",
          name: "money",
          onChange,
        },
        true
      );

      const input = wrapper.find("input");

      input.simulate("change", {
        // create element with all the necessary attributes for
        // parsing value
        target: createInputElement({ ...input.props(), value: maskedValue }),
      });
      expect(updateFields.mock.calls[0][0].money).toBe(expectedValue);
    });
  });
});
