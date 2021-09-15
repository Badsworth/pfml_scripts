import React from "react";
import { create } from "react-test-renderer";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import Button, { Props as ButtonProps } from "../../src/components/Button";

// Make all optional for passed props so we
// only have to pass what we want to test
type PassedProps = {
  className?: string;
  disabled?: boolean;
  onClick?: Function;
  children?: React.ReactNode;
};

const renderComponent = (passedProps: PassedProps = {}) => {
  // Prop defaults
  const props: ButtonProps = {
    onClick: jest.fn(),
    // Overwrite defaults with passed props
    ...passedProps,
  };

  return render(<Button {...props} />);
};

describe("Button", () => {
  test("renders the default component", () => {
    const props: ButtonProps = {
      onClick: jest.fn(),
    };

    const component = create(<Button {...props} />).toJSON();
    expect(component).toMatchSnapshot();
  });

  test("adds classes to component when `className` prop is used", () => {
    renderComponent({
      className: "test-one test-two",
    });

    expect(screen.getByTestId("button")).toHaveClass("test-one");
    expect(screen.getByTestId("button")).toHaveClass("test-two");
  });

  test("button is disabled when disabled prop is true", () => {
    const onClick = jest.fn();

    renderComponent({
      disabled: true,
      onClick: onClick,
    });

    userEvent.click(screen.getByTestId("button"));

    expect(onClick).toHaveBeenCalledTimes(0);
    expect(screen.getByTestId("button")).toHaveAttribute("disabled");
  });

  test("renders the button with the passed child content", () => {
    renderComponent({
      children: <span>Cool Button</span>,
    });

    expect(screen.getByTestId("button")).toContainHTML(
      "<span>Cool Button</span>",
    );
  });

  test("fires onClick callback when button is clicked", () => {
    const onClick = jest.fn();

    renderComponent({
      onClick: onClick,
    });

    userEvent.click(screen.getByTestId("button"));

    expect(onClick).toHaveBeenCalledTimes(1);
  });
});
