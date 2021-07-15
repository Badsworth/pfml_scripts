import { simulateEvents, testHook } from "../../test-utils";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import EmployeeNotice from "../../../src/components/employers/EmployeeNotice";
import React from "react";
import { shallow } from "enzyme";
import useFunctionalInputProps from "../../../src/hooks/useFunctionalInputProps";

describe("EmployeeNotice", () => {
  const updateFields = jest.fn();
  let getFunctionalInputProps;

  function render(givenProps = {}) {
    const defaultProps = {
      employeeNoticeInput: undefined,
      fraudInput: "No",
      getFunctionalInputProps,
      updateFields,
    };
    const props = { ...defaultProps, ...givenProps };

    return shallow(<EmployeeNotice {...props} />);
  }

  beforeEach(() => {
    testHook(() => {
      getFunctionalInputProps = useFunctionalInputProps({
        appErrors: new AppErrorInfoCollection(),
        formState: { fraud: "No", employee_notice: undefined },
        updateFields,
      });
    });
  });

  it("renders the component", () => {
    const wrapper = render();
    expect(wrapper).toMatchSnapshot();
  });

  it("does not select any option by default", () => {
    const wrapper = render();
    const choices = wrapper.find("InputChoiceGroup").prop("choices");

    for (const choice of choices) {
      expect(choice.checked).toBe(false);
    }
  });

  it("unselects and disables options if fraud is reported", () => {
    const wrapper = render({ fraudInput: "Yes" });

    const choices = wrapper.find("InputChoiceGroup").prop("choices");

    for (const choice of choices) {
      expect(choice.checked).toBe(false);
      expect(choice.disabled).toBe(true);
    }
  });

  it('calls "updateFields" when fraud choice has changed', () => {
    const wrapper = render();
    const { changeRadioGroup } = simulateEvents(wrapper);

    changeRadioGroup("employee_notice", "Yes");
    changeRadioGroup("employee_notice", "No");

    expect(updateFields).toHaveBeenCalledTimes(2);
    expect(updateFields).toHaveBeenNthCalledWith(1, { employee_notice: "Yes" });
    expect(updateFields).toHaveBeenNthCalledWith(2, { employee_notice: "No" });
  });
});
