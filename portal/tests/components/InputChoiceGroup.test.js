import { render, screen } from "@testing-library/react";

import InputChoiceGroup from "../../src/components/InputChoiceGroup";
import React from "react";
import userEvent from "@testing-library/user-event";

describe("InputChoiceGroup", () => {
  const defaultProps = {
    choices: [
      { label: "Foo", value: "foo" },
      { label: "Bar", value: "bar" },
    ],
    label: "Foobar",
    name: "foo-bar",
  };

  describe("InputChoiceGroup rendering", () => {
    it("renders groups using a `fieldset` element", () => {
      render(<InputChoiceGroup {...defaultProps} />);
      const inputChoiceGroup = screen.getByRole("group");

      expect(inputChoiceGroup).toBeInTheDocument();
    });

    it("renders a `fieldset` with `legend` element", () => {
      render(<InputChoiceGroup {...defaultProps} />);
      const legendElement = screen.getByRole("group", {
        name: defaultProps.label,
      });

      expect(legendElement).toBeInTheDocument();
    });

    it("renders an `InputChoice` to display options", () => {
      render(<InputChoiceGroup {...defaultProps} />);
      const inputChoices = screen.getAllByRole("checkbox");

      inputChoices.forEach((inputChoice) => {
        expect(inputChoice).toBeInTheDocument();
      });
    });
  });

  describe("InputChoiceGroup attributes", () => {
    it("sets the name attribute on each `InputChoice`", () => {
      render(<InputChoiceGroup {...defaultProps} />);
      const inputChoices = screen.getAllByRole("checkbox");

      inputChoices.forEach((inputChoice) => {
        expect(inputChoice).toHaveAttribute("name", defaultProps.name);
      });
    });

    it("sets `checkbox` as default `type` attribute on `InputChoice`", () => {
      render(<InputChoiceGroup {...defaultProps} />);
      const inputChoices = screen.getAllByRole("checkbox");

      inputChoices.forEach((inputChoice) => {
        expect(inputChoice).toHaveAttribute("type", "checkbox");
      });
    });

    it("uses `radio` when set with `type` attribute on `InputChoice`", () => {
      render(<InputChoiceGroup {...defaultProps} type="radio" />);
      const inputChoices = screen.getAllByRole("radio");

      inputChoices.forEach((inputChoice) => {
        expect(inputChoice).toHaveAttribute("type", "radio");
      });
    });
  });

  describe("InputChoiceGroup error messages", () => {
    const errorMsg = "error message";
    it("passes errorMsg to FormLabel when provided", () => {
      render(<InputChoiceGroup {...defaultProps} errorMsg={errorMsg} />);
      const formLabel = screen.getByText(errorMsg);

      expect(formLabel).toBeInTheDocument();
      expect(formLabel).toMatchSnapshot();
    });

    it("adds error class to the form group", () => {
      render(<InputChoiceGroup {...defaultProps} errorMsg={errorMsg} />);
      const inputChoiceGroup = screen.getByRole("group");

      expect(inputChoiceGroup).toHaveClass("usa-form-group--error");
    });

    it("does not add error class to the form group when there is no error", () => {
      render(<InputChoiceGroup {...defaultProps} />);
      const inputChoiceGroup = screen.getByRole("group");

      expect(inputChoiceGroup).not.toHaveClass("usa-form-group--error");
    });
  });

  it("calls `onChange` on click, when `onChange` is provided", () => {
    const handleChange = jest.fn();
    render(<InputChoiceGroup {...defaultProps} onChange={handleChange} />);
    const inputChoices = screen.getAllByRole("checkbox");

    inputChoices.forEach((inputChoice) => {
      userEvent.click(inputChoice);
      expect(handleChange).toHaveBeenCalled();
    });
  });
});
