import { simulateEvents, testHook } from "../../test-utils";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import FraudReport from "../../../src/components/employers/FraudReport";
import React from "react";
import { shallow } from "enzyme";
import useFunctionalInputProps from "../../../src/hooks/useFunctionalInputProps";

describe("FraudReport", () => {
  const updateFields = jest.fn();
  let getFunctionalInputProps;

  beforeEach(() => {
    testHook(() => {
      getFunctionalInputProps = useFunctionalInputProps({
        appErrors: new AppErrorInfoCollection(),
        formState: {},
        updateFields,
      });
    });
  });

  function render(givenProps = {}) {
    const defaultProps = {
      fraudInput: undefined,
      getFunctionalInputProps,
    };
    const props = { ...defaultProps, ...givenProps };
    return shallow(<FraudReport {...props} />);
  }

  it("does not select any option by default", () => {
    const wrapper = render();
    const choices = wrapper.find("InputChoiceGroup").prop("choices");

    for (const choice of choices) {
      expect(choice.checked).toBe(false);
    }
  });

  it("renders just the input choices by default", () => {
    const wrapper = render();
    expect(wrapper.find("ConditionalContent").prop("visible")).toBe(false);
    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });

  it('calls "updateFields" when the decision has changed', () => {
    const wrapper = render();
    const { changeRadioGroup } = simulateEvents(wrapper);

    changeRadioGroup("fraud", "Yes");
    changeRadioGroup("fraud", "No");

    expect(updateFields).toHaveBeenCalledTimes(2);
    expect(updateFields).toHaveBeenNthCalledWith(1, { fraud: "Yes" });
    expect(updateFields).toHaveBeenNthCalledWith(2, { fraud: "No" });
  });

  it("renders the alert if fraud is reported", () => {
    const wrapper = render({ fraudInput: "Yes" });

    expect(wrapper.find("ConditionalContent").prop("visible")).toBe(true);
    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });
});
