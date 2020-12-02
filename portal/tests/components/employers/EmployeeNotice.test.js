import { mount, shallow } from "enzyme";
import EmployeeNotice from "../../../src/components/employers/EmployeeNotice";
import React from "react";
import { simulateEvents } from "../../test-utils";

describe("EmployeeNotice", () => {
  let wrapper;
  const onChange = jest.fn();

  beforeEach(() => {
    wrapper = shallow(<EmployeeNotice fraud="No" onChange={onChange} />);
  });

  it("renders the component", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("does not select any option by default", () => {
    const choices = wrapper.find("InputChoiceGroup").prop("choices");

    for (const choice of choices) {
      expect(choice.checked).toBe(false);
    }
  });

  it("unselects and disables options if fraud is reported", () => {
    wrapper = shallow(<EmployeeNotice fraud="Yes" onChange={onChange} />);

    const choices = wrapper.find("InputChoiceGroup").prop("choices");

    for (const choice of choices) {
      expect(choice.checked).toBe(false);
      expect(choice.disabled).toBe(true);
    }
  });

  it('calls "onChange" when fraud choice has changed', () => {
    wrapper = mount(<EmployeeNotice fraud="No" onChange={onChange} />);
    const { changeRadioGroup } = simulateEvents(wrapper);

    changeRadioGroup("employeeNotice", "Yes");
    changeRadioGroup("employeeNotice", "No");

    expect(onChange).toHaveBeenCalledTimes(3);
    expect(onChange).toHaveBeenNthCalledWith(1, undefined);
    expect(onChange).toHaveBeenNthCalledWith(2, "Yes");
    expect(onChange).toHaveBeenNthCalledWith(3, "No");
  });
});
