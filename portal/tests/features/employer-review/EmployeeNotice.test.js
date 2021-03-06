import { render, screen } from "@testing-library/react";
import EmployeeNotice from "../../../src/features/employer-review/EmployeeNotice";
import React from "react";
import { renderHook } from "@testing-library/react-hooks";
import useFunctionalInputProps from "../../../src/hooks/useFunctionalInputProps";

function setupGetFunctionalInputProps(updateFields) {
  let getFunctionalInputProps;

  renderHook(() => {
    getFunctionalInputProps = useFunctionalInputProps({
      errors: [],
      formState: {},
      updateFields,
    });
  });

  return getFunctionalInputProps;
}

function renderComponent(customProps = {}) {
  const updateFields = jest.fn();

  const props = {
    getFunctionalInputProps: setupGetFunctionalInputProps(updateFields),
    updateFields,
    ...customProps,
  };

  return render(<EmployeeNotice {...props} />);
}

describe("EmployeeNotice", () => {
  it("renders the component", () => {
    const { container } = renderComponent();

    expect(container).toMatchSnapshot();
  });

  it("does not select any option by default", () => {
    renderComponent();
    const choices = screen.getAllByRole("radio");

    for (const choice of choices) {
      expect(choice.checked).toBe(false);
      expect(choice).toBeEnabled();
    }
  });

  it("unselects and disables options if fraud is reported", () => {
    renderComponent({ fraudInput: "Yes" });
    const choices = screen.getAllByRole("radio");

    for (const choice of choices) {
      expect(choice.checked).toBe(false);
      expect(choice).toBeDisabled();
    }
  });

  it("resets form's 'employee_notice' if changing from fraud to not fraud", () => {
    const updateFields = jest.fn();
    const props = {
      getFunctionalInputProps: setupGetFunctionalInputProps(updateFields),
      updateFields,
    };

    const { rerender } = render(<EmployeeNotice {...props} fraudInput="Yes" />);
    expect(props.updateFields).toHaveBeenCalledTimes(1); // on mount, because Fraud = Yes

    rerender(<EmployeeNotice {...props} fraudInput="No" />);

    expect(props.updateFields).toHaveBeenCalledTimes(2); // another time when Fraud prop changes
    expect(props.updateFields).toHaveBeenLastCalledWith({
      employee_notice: undefined,
    });
  });
});
