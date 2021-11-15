import { render, screen } from "@testing-library/react";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import EmployerDecision from "../../../src/components/employers/EmployerDecision";
import React from "react";
import { renderHook } from "@testing-library/react-hooks";
import useFunctionalInputProps from "../../../src/hooks/useFunctionalInputProps";
import userEvent from "@testing-library/user-event";

describe("EmployerDecision", () => {
  const updateFields = jest.fn();
  let getFunctionalInputProps;

  beforeEach(() => {
    renderHook(() => {
      getFunctionalInputProps = useFunctionalInputProps({
        appErrors: new AppErrorInfoCollection(),
        formState: { employerDecision: "Approve" },
        updateFields,
      });
    });
  });

  function renderComponent(customProps = {}) {
    const defaultProps = {
      employerDecision: undefined,
      fraud: undefined,
      getFunctionalInputProps,
      updateFields,
      ...customProps,
    };
    return render(<EmployerDecision {...defaultProps} />);
  }

  it("renders the component", () => {
    const { container } = renderComponent();
    expect(container.firstChild).toMatchSnapshot();
  });

  it("updates the form state on change", () => {
    renderComponent();
    userEvent.click(screen.getByRole("radio", { name: "Approve" }));
    userEvent.click(
      screen.getByRole("radio", { name: "Deny (explain below)" })
    );
    expect(updateFields).toHaveBeenCalledTimes(2);
    expect(updateFields).toHaveBeenNthCalledWith(1, {
      employer_decision: "Approve",
    });
    expect(updateFields).toHaveBeenNthCalledWith(2, {
      employer_decision: "Deny",
    });
  });

  it("when fraud is reported, calls updateFields with employer decision of deny", () => {
    renderComponent({ fraud: "Yes" });
    expect(updateFields).toHaveBeenCalledWith({ employer_decision: "Deny" });
  });

  it('when fraud is reported, disables the "Approve" option', () => {
    renderComponent({ fraud: "Yes" });
    expect(screen.getByRole("radio", { name: "Approve" })).toBeDisabled();
  });

  it('when fraud report is reverted, re-enables the "Approve" option', () => {
    const { rerender } = renderComponent({ fraud: "Yes" });
    const props = {
      employerDecision: undefined,
      fraud: undefined,
      getFunctionalInputProps,
      updateFields,
    };
    rerender(<EmployerDecision {...props} />);
    expect(screen.getByRole("radio", { name: "Approve" })).toBeEnabled();
  });

  it("when fraud report is reverted, clears the selection", () => {
    const { rerender } = renderComponent({ fraud: "Yes" });
    const props = {
      employerDecision: undefined,
      fraud: undefined,
      getFunctionalInputProps,
      updateFields,
    };
    rerender(<EmployerDecision {...props} />);

    const choices = screen.getAllByRole("radio");
    for (const choice of choices) {
      expect(choice.checked).toBe(false);
    }
  });
});
