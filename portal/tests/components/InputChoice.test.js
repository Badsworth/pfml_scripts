import { render, screen } from "@testing-library/react";

import InputChoice from "../../src/components/InputChoice";
import React from "react";
import userEvent from "@testing-library/user-event";

describe("InputChoice", () => {
  const defaultProps = {
    label: "foo",
    name: "bar",
    value: "foobar",
  };

  describe("InputChoice attributes", () => {
    it("creates `id` attribute if `id` is not provided", () => {
      render(<InputChoice {...defaultProps} />);
      const input = screen.getByRole("checkbox");

      expect(input).toHaveAttribute("id");
      expect(input).toMatchSnapshot();
    });

    it("sets `aria-controls` attribute when provided", () => {
      render(<InputChoice {...defaultProps} ariaControls="foobar-aria" />);
      const input = screen.getByRole("checkbox");

      expect(input).toHaveAttribute("aria-controls");
      expect(input).toMatchSnapshot();
    });

    it("sets the `name` attribute when provided", () => {
      render(<InputChoice {...defaultProps} />);
      const input = screen.getByRole("checkbox");

      expect(input).toHaveAttribute("name", defaultProps.name);
      expect(input).toMatchSnapshot();
    });

    it("sets the `value` attribute when provided", () => {
      render(<InputChoice {...defaultProps} />);
      const input = screen.getByRole("checkbox");

      expect(input).toMatchInlineSnapshot(`
        <input
          class="usa-checkbox__input"
          id="InputChoice4"
          name="bar"
          type="checkbox"
          value="foobar"
        />
      `);
    });

    it("sets the `disabled` attribute when provided", () => {
      render(<InputChoice {...defaultProps} disabled />);
      const input = screen.getByRole("checkbox");

      expect(input).toBeDisabled();
      expect(input).toMatchSnapshot();
    });
  });

  describe("InputChoice class names", () => {
    it("sets the parent container's className when provided", () => {
      render(<InputChoice {...defaultProps} className="foo" />);
      const inputWrapper = screen.getByRole("checkbox").closest("div");

      expect(inputWrapper).toBeInTheDocument();
      expect(inputWrapper).toHaveClass("foo");
      expect(inputWrapper).toMatchSnapshot();
    });

    it("sets the correct default input class name", () => {
      render(<InputChoice {...defaultProps} />);
      const input = screen.getByRole("checkbox");

      expect(input).toHaveClass("usa-checkbox__input");
      expect(input).toMatchSnapshot();
    });
  });

  describe("InputChoice children", () => {
    it("renders the label element", () => {
      render(<InputChoice {...defaultProps} />);
      const label = screen.getByText(/foo/);

      expect(label).toHaveClass("usa-checkbox__label");
      expect(label).toBeInTheDocument();
      expect(label).toMatchSnapshot();
    });

    it("renders the hint when provided", () => {
      render(<InputChoice {...defaultProps} hint="Foobar Hint" />);
      const hint = screen.getByText(/foobar hint/i);

      expect(hint).toBeInTheDocument();
      expect(hint).toMatchSnapshot();
    });
  });

  describe("InputChoice `types`", () => {
    it("sets the correct default input type", () => {
      render(<InputChoice {...defaultProps} />);
      const input = screen.getByRole("checkbox");

      expect(input).toBeInTheDocument();
      expect(input).toMatchSnapshot();
    });

    it("sets input type to radio when `type` is `radio`", () => {
      render(<InputChoice {...defaultProps} type="radio" />);
      const input = screen.getByRole("radio");

      expect(input).toHaveClass("usa-radio__input");
      expect(input).toBeInTheDocument();
      expect(input).toMatchSnapshot();
    });
  });

  describe("InputChoice onChange", () => {
    it("calls `onChange` on click, when `onChange` is provided", () => {
      const handleChange = jest.fn();
      render(<InputChoice {...defaultProps} onChange={handleChange} />);
      const input = screen.getByRole("checkbox");
      userEvent.click(input);

      expect(handleChange).toHaveBeenCalled();
      expect(input).toMatchSnapshot();
    });
  });
});
