import { render, screen } from "@testing-library/react";
import ErrorInfo from "../../../src/models/ErrorInfo";
import React from "react";
import WeeklyHoursWorkedRow from "../../../src/features/employer-review/WeeklyHoursWorkedRow";
import userEvent from "@testing-library/user-event";

const clickAmendButton = () =>
  userEvent.click(screen.getByRole("button", { name: /Amend/ }));

const clickCancelAmendButton = () =>
  userEvent.click(screen.getByRole("button", { name: /Cancel amendment/ }));

const getInputElement = () =>
  screen.getByLabelText(
    /On average, how many hours does the employee work each week\?/
  );

describe("WeeklyHoursWorkedRow", () => {
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
    errors: [],
    clearField,
    getField,
    getFunctionalInputProps,
    initialHoursWorkedPerWeek: 40,
    updateFields,
  };

  it("renders without the amendment form open", () => {
    const { container } = render(<WeeklyHoursWorkedRow {...defaultProps} />);
    expect(container).toMatchSnapshot();
  });

  it('opens the amendment form when "Amend" is clicked', () => {
    const { container } = render(<WeeklyHoursWorkedRow {...defaultProps} />);

    clickAmendButton();

    const amendTitle = screen.getByRole("heading", {
      level: 4,
      name: /Amend weekly hours worked/,
    });
    const inputElement = getInputElement();
    expect(amendTitle).toBeInTheDocument();
    expect(inputElement.value).toBe("40");
    expect(container).toMatchSnapshot();
  });

  it("updates the formState when the amendment form is typed in", () => {
    render(<WeeklyHoursWorkedRow {...defaultProps} />);
    clickAmendButton();

    userEvent.type(getInputElement(), "78");

    expect(functionalOnChange).toHaveBeenCalled();
  });

  describe('when "Cancel amendment" is clicked', () => {
    it("closes the amendment form", () => {
      render(<WeeklyHoursWorkedRow {...defaultProps} />);
      clickAmendButton();

      clickCancelAmendButton();

      expect(
        screen.queryByRole("heading", { level: 4 })
      ).not.toBeInTheDocument();
    });

    it("restores the original value", () => {
      render(<WeeklyHoursWorkedRow {...defaultProps} />);
      clickAmendButton();
      const inputElement = screen.getByLabelText(
        /On average, how many hours does the employee work each week\?/
      );
      userEvent.type(inputElement, "78");

      clickCancelAmendButton();

      expect(
        screen.queryByRole("heading", { level: 4 })
      ).not.toBeInTheDocument();
      expect(functionalOnChange).toHaveBeenCalled();
    });
  });

  describe("if there is a form error", () => {
    it("automatically opens the amendment form", () => {
      const errors = [
        new ErrorInfo({ name: "My error", message: "My message" }),
      ];

      render(<WeeklyHoursWorkedRow {...defaultProps} errors={errors} />);

      const amendTitle = screen.getByRole("heading", {
        level: 4,
        name: /Amend weekly hours worked/,
      });
      expect(amendTitle).toBeInTheDocument();
    });

    it("allows closing the opened amendment form", () => {
      const errors = [
        new ErrorInfo({ name: "My error", message: "My message" }),
      ];
      render(<WeeklyHoursWorkedRow {...defaultProps} errors={errors} />);

      clickCancelAmendButton();

      expect(
        screen.queryByRole("heading", { level: 4 })
      ).not.toBeInTheDocument();
    });
  });
});
