import { fireEvent, render, screen } from "@testing-library/react";
import AppErrorInfo from "../../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import React from "react";
import SupportingWorkDetails from "../../../src/components/employers/SupportingWorkDetails";
import userEvent from "@testing-library/user-event";

const clickAmendButton = () =>
  fireEvent.click(screen.getByRole("button", { name: /Amend/ }));

const clickCancelAmendButton = () =>
  fireEvent.click(screen.getByRole("button", { name: /Cancel amendment/ }));

const getInputElement = () =>
  screen.getByLabelText(
    /On average, how many hours does the employee work each week\?/
  );

describe("SupportingWorkDetails", () => {
  const formState = { hours_worked_per_week: 40 };
  const clearField = jest.fn();
  const getField = jest.fn();
  const functionalOnChange = jest.fn();
  const getFunctionalInputProps = jest.fn().mockImplementation((name) => ({
    errorMsg: undefined,
    name,
    onChange: functionalOnChange,
    value: formState[name],
  }));
  const updateFields = jest.fn();

  const defaultProps = {
    appErrors: new AppErrorInfoCollection(),
    clearField,
    getField,
    getFunctionalInputProps,
    initialHoursWorkedPerWeek: 40,
    updateFields,
  };

  it("renders without the amendment form open", () => {
    const { container } = render(<SupportingWorkDetails {...defaultProps} />);
    expect(container).toMatchSnapshot();
  });

  it('opens the amendment form when "Amend" is clicked', () => {
    const { container } = render(<SupportingWorkDetails {...defaultProps} />);

    clickAmendButton();

    const amendTitle = screen.getByRole("heading", {
      level: 4,
      name: /Amend weekly hours worked/,
    });
    const inputElement = getInputElement();
    expect(amendTitle).toBeTruthy();
    expect(inputElement.value).toBe("40");
    expect(container).toMatchSnapshot();
  });

  it("updates the formState when the amendment form is typed in", () => {
    render(<SupportingWorkDetails {...defaultProps} />);
    clickAmendButton();

    userEvent.type(getInputElement(), "78");

    expect(functionalOnChange).toHaveBeenCalled();
  });

  describe('when "Cancel amendment" is clicked', () => {
    it("closes the amendment form", () => {
      render(<SupportingWorkDetails {...defaultProps} />);
      clickAmendButton();

      clickCancelAmendButton();

      expect(
        screen.queryByRole("heading", { level: 4 })
      ).not.toBeInTheDocument();
    });

    it("restores the original value", () => {
      render(<SupportingWorkDetails {...defaultProps} />);
      clickAmendButton();
      const inputElement = screen.getByLabelText(
        /On average, how many hours does the employee work each week\?/
      );
      userEvent.type(inputElement, "78");

      clickCancelAmendButton();

      expect(screen.queryByRole("heading", { level: 4 })).toBeNull();
      expect(functionalOnChange).toHaveBeenCalled();
    });
  });

  describe("if there is a form error", () => {
    it("automatically opens the amendment form", () => {
      const appErrors = new AppErrorInfoCollection([
        new AppErrorInfo({ name: "My error", message: "My message" }),
      ]);

      render(<SupportingWorkDetails {...defaultProps} appErrors={appErrors} />);

      const amendTitle = screen.getByRole("heading", {
        level: 4,
        name: /Amend weekly hours worked/,
      });
      expect(amendTitle).toBeTruthy();
    });

    it("allows closing the opened amendment form", () => {
      const appErrors = new AppErrorInfoCollection([
        new AppErrorInfo({ name: "My error", message: "My message" }),
      ]);
      render(<SupportingWorkDetails {...defaultProps} appErrors={appErrors} />);

      clickCancelAmendButton();

      expect(
        screen.queryByRole("heading", { level: 4 })
      ).not.toBeInTheDocument();
    });
  });
});
