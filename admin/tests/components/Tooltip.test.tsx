import React from "react";
import { create } from "react-test-renderer";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import Tooltip, { Props as TooltipProps } from "../../src/components/Tooltip";

// Make all optional for passed props so we
// only have to pass what we want to test
type PassedProps = {
  position?: "top" | "bottom" | "left" | "right";
  children?: React.ReactNode;
};

const renderComponent = (passedProps: PassedProps = {}) => {
  // Prop defaults
  const props: TooltipProps = {
    children: "This is a test tooltip.",
    // Overwrite defaults with passed props
    ...passedProps,
  };

  return render(<Tooltip {...props} />);
};

describe("Tooltip", () => {
  test("renders the default component", () => {
    const props: TooltipProps = {
      children: "This is a test tooltip.",
    };

    const component = create(<Tooltip {...props} />).toJSON();
    expect(component).toMatchSnapshot();
  });

  test("renders with right position by default", () => {
    renderComponent();

    expect(screen.getByTestId("tooltip")).toHaveClass("tooltip--right");
  });

  test("renders with left position when 'left' is passed through `position` prop", () => {
    renderComponent({
      position: "left",
    });

    expect(screen.getByTestId("tooltip")).toHaveClass("tooltip--left");
  });

  test("renders with top position when 'top' is passed through `position` prop", () => {
    renderComponent({
      position: "top",
    });

    expect(screen.getByTestId("tooltip")).toHaveClass("tooltip--top");
  });

  test("renders with bottom position when 'bottom' is passed through `position` prop", () => {
    renderComponent({
      position: "bottom",
    });

    expect(screen.getByTestId("tooltip")).toHaveClass("tooltip--bottom");
  });
});
