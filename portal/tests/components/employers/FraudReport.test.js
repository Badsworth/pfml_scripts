import { render, screen } from "@testing-library/react";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import FraudReport from "../../../src/components/employers/FraudReport";
import React from "react";
import { renderHook } from "@testing-library/react-hooks";
import useFunctionalInputProps from "../../../src/hooks/useFunctionalInputProps";
import userEvent from "@testing-library/user-event";

describe("FraudReport", () => {
  const updateFields = jest.fn();
  let getFunctionalInputProps;

  beforeEach(() => {
    renderHook(() => {
      getFunctionalInputProps = useFunctionalInputProps({
        appErrors: new AppErrorInfoCollection(),
        formState: {},
        updateFields,
      });
    });
  });

  function renderComponent(customProps = {}) {
    const defaultProps = {
      fraudInput: undefined,
      getFunctionalInputProps,
      ...customProps,
    };
    return render(<FraudReport {...defaultProps} />);
  }

  it("does not select any option by default", () => {
    renderComponent();
    const choices = screen.getAllByRole("radio");
    for (const choice of choices) {
      expect(choice.checked).toBe(false);
    }
  });

  it("renders just the input choices by default", () => {
    renderComponent();
    expect(
      screen.queryByText(/You are reporting fraud./)
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(
        /We take allegations about fraud seriously. Selecting this will begin further investigation. Please only select if you are convinced this is fraudulent./
      )
    ).not.toBeInTheDocument();
  });

  it('calls "updateFields" when the decision has changed', () => {
    renderComponent();
    const yes = screen.getByRole("radio", { name: "Yes (explain below)" });
    const no = screen.getByRole("radio", { name: "No" });

    userEvent.click(yes);
    userEvent.click(no);
    expect(updateFields).toHaveBeenCalledTimes(2);
    expect(updateFields).toHaveBeenNthCalledWith(1, { fraud: "Yes" });
    expect(updateFields).toHaveBeenNthCalledWith(2, { fraud: "No" });
  });

  it("renders the alert if fraud is reported", () => {
    renderComponent({ fraudInput: "Yes" });
    expect(screen.getByText(/You are reporting fraud./)).toBeInTheDocument();
    expect(
      screen.getByText(
        /We take allegations about fraud seriously. Selecting this will begin further investigation. Please only select if you are convinced this is fraudulent./
      )
    ).toBeInTheDocument();
  });
});
