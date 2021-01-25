import { mount, shallow } from "enzyme";
import FraudReport from "../../../src/components/employers/FraudReport";
import React from "react";
import { simulateEvents } from "../../test-utils";

describe("FraudReport", () => {
  let wrapper;
  const onChange = jest.fn();

  beforeEach(() => {
    wrapper = shallow(<FraudReport onChange={onChange} />);
  });

  it("does not select any option by default", () => {
    const choices = wrapper.find("InputChoiceGroup").prop("choices");

    for (const choice of choices) {
      expect(choice.checked).toBe(false);
    }
  });

  it("renders just the input choices by default", () => {
    expect(wrapper.find("ConditionalContent").prop("visible")).toBe(false);
    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });

  it('renders the alert if "Yes" is selected', () => {
    const { changeRadioGroup } = simulateEvents(wrapper);

    changeRadioGroup("isFraud", "Yes");

    expect(wrapper.find("ConditionalContent").prop("visible")).toBe(true);
    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });

  it('calls "onChange" when the decision has changed', () => {
    wrapper = mount(<FraudReport onChange={onChange} />);
    const { changeRadioGroup } = simulateEvents(wrapper);

    changeRadioGroup("isFraud", "Yes");
    changeRadioGroup("isFraud", "No");

    expect(onChange).toHaveBeenCalledTimes(2);
    expect(onChange).toHaveBeenNthCalledWith(1, "Yes");
    expect(onChange).toHaveBeenNthCalledWith(2, "No");
  });
});
