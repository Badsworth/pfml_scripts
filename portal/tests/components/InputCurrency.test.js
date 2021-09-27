import { render, screen } from "@testing-library/react";

import InputCurrency from "../../src/components/InputCurrency";
import React from "react";

describe("InputCurrency", () => {
  const defaultProps = {
    label: "Foobar",
    name: "foobar",
    onChange: jest.fn(),
  };

  it("displays input, label and hint to the user", () => {
    render(
      <InputCurrency {...defaultProps} label="Foo" name="bar" hint="Foobar" />
    );

    const hint = screen.getByText("Foobar");
    const input = screen.getByRole("textbox");
    const label = screen.getByText("Foo");

    expect(label).toBeInTheDocument();
    expect(input).toHaveAttribute("name", "bar");
    expect(hint).toBeInTheDocument();
  });

  describe("InputCurrency values", () => {
    it("displays null values as an empty string", () => {
      render(<InputCurrency {...defaultProps} value={null} />);

      const input = screen.getByRole("textbox");
      expect(input).toHaveValue("");
    });

    it("displays integer values as an integer string", () => {
      render(<InputCurrency {...defaultProps} value={25000} />);

      const input = screen.getByRole("textbox");
      expect(input).toHaveValue("25,000");
    });

    it("displays float (decimal) values as a string", () => {
      render(<InputCurrency {...defaultProps} value={1000000.55} />);

      const input = screen.getByRole("textbox");
      expect(input).toHaveValue("1,000,000.55");
    });

    it("displays negative values as a string", () => {
      render(<InputCurrency {...defaultProps} value={-5050.25} />);

      const input = screen.getByRole("textbox");
      expect(input).toHaveValue("-5,050.25");
    });
  });
});
