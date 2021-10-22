import { render, screen } from "@testing-library/react";
import FormLabel from "../../src/components/FormLabel";
import React from "react";

describe("FormLabel", () => {
  const text = "Form label text";

  describe("FormLabel rendering", () => {
    it("renders the form label and its children", () => {
      render(<FormLabel>{text}</FormLabel>);
      expect(screen.getByText(text)).toBeInTheDocument();
    });
  });

  describe("FormLabel attributes", () => {
    const inputId = "foo";

    it("sets the label's `for` attribute when component is a `label`", () => {
      render(<FormLabel inputId={inputId}>{text}</FormLabel>);
      expect(screen.getByText(text)).toHaveAttribute("for", inputId);
    });

    it("doesn't set the label's `for` attribute when component is a `legend`", () => {
      render(
        <FormLabel component="legend" inputId={inputId}>
          {text}
        </FormLabel>
      );
      expect(screen.getByText(text)).not.toHaveAttribute("for");
    });

    it("doesn't set the label's `id` attribute when `inputId` is not set", () => {
      render(<FormLabel>{text}</FormLabel>);
      expect(screen.getByText(text)).not.toHaveAttribute("id");
    });
  });

  describe("FormLabel labelClassName", () => {
    const labelClassName = "custom-class-name";

    it("renders custom label class names as expected", () => {
      render(<FormLabel labelClassName={labelClassName}>{text}</FormLabel>);
      expect(screen.getByText(text)).toHaveClass(labelClassName);
    });

    it("custom label class names override the `text-bold` class", () => {
      render(<FormLabel labelClassName={labelClassName}>{text}</FormLabel>);
      expect(screen.getByText(text)).not.toHaveClass("text-bold");
    });
  });

  describe("FormLabel Hint", () => {
    const hintText = "hint text";

    it("renders the hint when provided", () => {
      render(<FormLabel hint={hintText}>{text}</FormLabel>);
      expect(screen.getByText(hintText)).toBeInTheDocument();
    });

    it("doesn't render the hint when it's not provided", () => {
      render(<FormLabel hint={hintText}>{text}</FormLabel>);
      const hint = screen.getByText(hintText);
      expect(hint).toBeInTheDocument();
    });
  });

  describe("FormLabel class lists", () => {
    it("renders component `label` with expected classes when small", () => {
      render(<FormLabel small>{text}</FormLabel>);
      expect(screen.getByText(text)).toHaveClass(
        "font-heading-xs",
        "measure-5"
      );
    });

    it("renders component `legend` with expected classes when small", () => {
      render(
        <FormLabel component="legend" small>
          {text}
        </FormLabel>
      );
      expect(screen.getByText(text)).toHaveClass(
        "font-heading-xs",
        "measure-5"
      );
    });

    it("renders the example text with expected classes", () => {
      const exampleText = "example text";
      render(<FormLabel example={exampleText}>{text}</FormLabel>);
      const example = screen.getByText(exampleText);

      expect(example).toHaveClass(
        "display-block",
        "line-height-sans-5",
        "measure-5",
        "text-base-dark",
        "usa-hint"
      );
    });

    it("renders the optional text with expected classes", () => {
      const optionalText = "optional text";
      render(<FormLabel optionalText={optionalText}>{text}</FormLabel>);
      const optionalItem = screen.getByText(optionalText);

      expect(optionalItem).toHaveClass(
        "text-base-dark",
        "text-normal",
        "usa-hint"
      );
    });
  });

  describe("FormLabel errorMsg", () => {
    it("renders error message when `errorMsg` is set", () => {
      const errorMsg = "error message";
      render(<FormLabel errorMsg={errorMsg}>{text}</FormLabel>);
      const error = screen.getByText(errorMsg);

      expect(error).toBeInTheDocument();
    });
  });
});
