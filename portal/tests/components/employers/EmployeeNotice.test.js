import { mount, shallow } from "enzyme";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import EmployeeNotice from "../../../src/components/employers/EmployeeNotice";
import React from "react";
import { act } from "react-dom/test-utils";
import { testHook } from "../../test-utils";
import useFunctionalInputProps from "../../../src/hooks/useFunctionalInputProps";

describe("EmployeeNotice", () => {
  const updateFields = jest.fn();
  let getFunctionalInputProps;

  function render(givenProps = {}) {
    const defaultProps = {
      employeeNoticeInput: undefined,
      fraudInput: undefined,
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
        formState: {},
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

  it("resets form's 'employee_notice' if changing from fraud to not fraud", () => {
    const wrapper = mount(
      <EmployeeNotice
        employeeNoticeInput={undefined}
        fraudInput="Yes"
        getFunctionalInputProps={getFunctionalInputProps}
        updateFields={updateFields}
      />
    );
    act(() => {
      wrapper.setProps({ fraudInput: "No" });
    });
    wrapper.update();

    expect(updateFields).toHaveBeenCalledWith({ employee_notice: undefined });
  });
});
