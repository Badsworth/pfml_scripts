import FormLabel from "../../src/components/FormLabel";
import React from "react";
import { render } from "@testing-library/react";

describe("FormLabel", () => {
  const text = "Form label text";

  const expectElementClasses = (element, ...classList) => {
    classList.forEach((className) => {
      expect(element).toHaveClass(className);
    });
  };

  describe("FormLabel rendering", () => {
    it("renders the form label and its children", () => {
      const label = render(<FormLabel>{text}</FormLabel>);
      expect(label.getByText(text)).toBeInTheDocument();
    });
  });

  describe("FormLabel attributes", () => {
    const inputId = "foo";

    it("sets the label's `for` attribute when component is a `label`", () => {
      const label = render(<FormLabel inputId={inputId}>{text}</FormLabel>);
      expect(label.getByText(text)).toHaveAttribute("for", inputId);
    });

    it("doesn't set the label's `for` attribute when component is a `legend`", () => {
      const legend = render(
        <FormLabel component="legend" inputId={inputId}>
          {text}
        </FormLabel>
      );
      expect(legend.getByText(text)).not.toHaveAttribute("for");
    });

    it("doesn't set the label's `id` attribute when `inputId` is not set", () => {
      const label = render(<FormLabel>{text}</FormLabel>);
      expect(label.getByText(text)).not.toHaveAttribute("id");
    });
  });

  describe("FormLabel labelClassName", () => {
    const labelClassName = "custom-class-name";

    it("renders custom label class names as expected", () => {
      const label = render(
        <FormLabel labelClassName={labelClassName}>{text}</FormLabel>
      );
      expect(label.getByText(text)).toHaveClass(labelClassName);
    });

    it("custom label class names override the `text-bold` class", () => {
      const label = render(
        <FormLabel labelClassName={labelClassName}>{text}</FormLabel>
      );
      expect(label.getByText(text)).not.toHaveClass("text-bold");
    });
  });

  describe("FormLabel Hint", () => {
    const hintText = "hint text";

    it("renders the hint when provided", () => {
      const label = render(<FormLabel hint={hintText}>{text}</FormLabel>);
      expect(label.getByText(hintText)).toBeInTheDocument();
    });

    it("doesn't render the hint when it's not provided", () => {
      const label = render(<FormLabel hint={hintText}>{text}</FormLabel>);
      const hint = label.getByText(hintText);
      expect(hint).toBeInTheDocument();
    });
  });

  describe("FormLabel class lists", () => {
    it("renders component `label` with expected classes when small", () => {
      const label = render(<FormLabel small>{text}</FormLabel>);
      expectElementClasses(
        label.getByText(text),
        "font-heading-xs",
        "measure-5"
      );
    });

    it("renders component `legend` with expected classes when small", () => {
      const label = render(
        <FormLabel component="legend" small>
          {text}
        </FormLabel>
      );
      expectElementClasses(
        label.getByText(text),
        "font-heading-xs",
        "measure-5"
      );
    });

    it("renders the example text with expected classes", () => {
      const exampleText = "example text";
      const label = render(<FormLabel example={exampleText}>{text}</FormLabel>);
      const example = label.getByText(exampleText);

      expectElementClasses(
        example,
        "display-block",
        "line-height-sans-5",
        "measure-5",
        "text-base-dark",
        "usa-hint"
      );
    });

    it("renders the optional text with expected classes", () => {
      const optionalText = "optional text";
      const label = render(
        <FormLabel optionalText={optionalText}>{text}</FormLabel>
      );
      const optionalItem = label.getByText(optionalText);

      expectElementClasses(
        optionalItem,
        "text-base-dark",
        "text-normal",
        "usa-hint"
      );
    });
  });

  describe("FormLabel errorMsg", () => {
    it("renders error message when `errorMsg` is set", () => {
      const errorMsg = "error message";
      const label = render(<FormLabel errorMsg={errorMsg}>{text}</FormLabel>);
      const error = label.getByText(errorMsg);

      expect(error).toBeInTheDocument();
    });
  });
});
