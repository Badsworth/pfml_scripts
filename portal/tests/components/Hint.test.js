import Hint from "../../src/components/Hint";
import React from "react";
import { render } from "@testing-library/react";

describe("Hint", () => {
  const hintText = "Foobar";

  describe("Hint id attribute", () => {
    it("set the `id` attribute when inputId is set", () => {
      const { container } = render(<Hint inputId="foo">{hintText}</Hint>);
      const hint = container.querySelector("#foo_hint");

      expect(hint).toHaveAttribute("id", "foo_hint");
      expect(hint).toMatchSnapshot();
    });

    it("does not set the `id` attribute when inputId is not set", () => {
      const { getByText } = render(<Hint>{hintText}</Hint>);
      const hint = getByText(hintText);

      expect(hint).not.toHaveAttribute("id");
      expect(hint).toMatchSnapshot();
    });
  });

  describe("Hint class names", () => {
    it("renders correct default classes", () => {
      const { container } = render(<Hint inputId="foo">{hintText}</Hint>);
      const hint = container.querySelector("#foo_hint");

      expect(hint).toHaveClass(
        "display-block",
        "line-height-sans-5",
        "measure-5",
        "usa-intro"
      );
      expect(hint).toMatchSnapshot();
    });

    it("renders correct classes with `small` prop", () => {
      const { container } = render(
        <Hint inputId="foo" small>
          {hintText}
        </Hint>
      );
      const hint = container.querySelector("#foo_hint");

      expect(hint).toHaveClass(
        "display-block",
        "line-height-sans-5",
        "measure-5",
        "usa-hint",
        "text-base-darkest"
      );
      expect(hint).toMatchSnapshot();
    });

    it("adds class name when provided through props", () => {
      const { container } = render(<Hint className="foo">{hintText}</Hint>);
      const hint = container.querySelector(".foo");

      expect(hint).toBeInTheDocument();
      expect(hint).toHaveClass("foo");
      expect(hint).toMatchSnapshot();
    });
  });
});
