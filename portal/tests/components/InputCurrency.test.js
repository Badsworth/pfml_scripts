import InputCurrency from "../../src/components/InputCurrency";
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

  const component = <InputCurrency {...props} />;

  return {
    props,
    wrapper: shallow(component),
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

  it("propogates the number value for onChange events", () => {
    values.forEach(([expectedValue, maskedValue]) => {
      const { props, wrapper } = render({
        label: "Money",
        name: "money",
      });

      wrapper.find("InputNumber").simulate("change", {
        target: {
          name: "money",
          value: maskedValue,
        },
      });

      expect(props.onChange.mock.calls[0][0].target.value).toBe(expectedValue);
    });
  });
});
