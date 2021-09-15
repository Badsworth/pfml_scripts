import React from "react";
import { create } from "react-test-renderer";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import ActionCard, {
  Props as ActionCardProps,
} from "../../src/components/ActionCard";

// Make all optional for passed props so we
// only have to pass what we want to test
type PassedProps = {
  title?: string;
  description?: string;
  buttonText?: string;
  onButtonClick?: () => void;
};

const renderComponent = (passedProps: PassedProps = {}) => {
  // Prop defaults
  const props: ActionCardProps = {
    title: "Test Title",
    description: "Test description for action card",
    // Overwrite defaults with passed props
    ...passedProps,
  };

  return render(<ActionCard {...props} />);
};

describe("ActionCard", () => {
  test("renders the default component", () => {
    const props: ActionCardProps = {
      title: "Test Title",
      description: "Test description for action card",
    };

    const component = create(<ActionCard {...props} />).toJSON();
    expect(component).toMatchSnapshot();
  });

  test("renders the passed title text", () => {
    const title = "This is a passed title";
    renderComponent({
      title: title,
    });

    expect(screen.getByText(title)).toBeInTheDocument();
  });

  test("renders the passed description", () => {
    const description = "This is a passed description";
    renderComponent({
      description: description,
    });

    expect(screen.getByText(description)).toBeInTheDocument();
  });

  test("renders a button when `buttonText` and `onButtonClick` props are passed", () => {
    renderComponent({
      buttonText: "Test Button",
      onButtonClick: jest.fn(),
    });

    expect(
      screen.getByRole("button", { name: "Test Button" }),
    ).toBeInTheDocument();
  });

  test("does not render a button when `buttonText` and `onButtonClick` props are not passed", () => {
    renderComponent();

    expect(
      screen.queryByRole("button", { name: "Test Button" }),
    ).not.toBeInTheDocument();
  });

  test("calls `onButtonClick` callback prop when button is clicked", () => {
    const onButtonClick = jest.fn();

    renderComponent({
      buttonText: "Test Button",
      onButtonClick: onButtonClick,
    });

    userEvent.click(screen.getByRole("button", { name: "Test Button" }));

    expect(onButtonClick).toHaveBeenCalled();
  });
});
