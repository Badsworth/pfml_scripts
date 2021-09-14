import React from "react";
import { create } from "react-test-renderer";
import { fireEvent, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import ConfirmationDialog, {
  Props as ConfirmationDialogProps,
} from "../../src/components/ConfirmationDialog";

// Make all optional for passed props so we
// only have to pass what we want to test
type PassedProps = {
  title?: string;
  body?: string;
  handleCancelCallback?: Function;
  handleContinueCallback?: Function;
};

const renderComponent = (passedProps: PassedProps = {}) => {
  // Prop defaults
  const props: ConfirmationDialogProps = {
    title: "Test Title",
    body: "This is a test body.",
    handleCancelCallback: jest.fn(),
    handleContinueCallback: jest.fn(),
    // Overwrite defaults with passed props
    ...passedProps,
  };

  return render(<ConfirmationDialog {...props} />);
};

describe("ConfirmationDialog", () => {
  test("default component renders correctly", () => {
    const props: ConfirmationDialogProps = {
      title: "Test Title",
      body: "This is a test body.",
      handleCancelCallback: jest.fn(),
      handleContinueCallback: jest.fn(),
    };

    const component = create(<ConfirmationDialog {...props} />).toJSON();
    expect(component).toMatchSnapshot();
  });

  test("renders the passed text for `title`", () => {
    renderComponent({
      title: "A Really Cool Title",
    });

    expect(screen.getByTestId("confirmation-dialog-title")).toHaveTextContent(
      "A Really Cool Title?",
    );
  });

  test("renders the passed text for `body`", () => {
    renderComponent({
      body: "The thing with the guy at the place.",
    });

    expect(screen.getByTestId("confirmation-dialog-body")).toHaveTextContent(
      "The thing with the guy at the place.",
    );
  });

  test("continue callback function fires when continue button is clicked", () => {
    const handleContinueCallback = jest.fn();

    renderComponent({
      handleContinueCallback: handleContinueCallback,
    });

    fireEvent.click(screen.getByText("Continue"));

    expect(handleContinueCallback).toHaveBeenCalledTimes(1);
  });

  test("cancel callback function fires when cancel button is clicked", () => {
    const handleCancelCallback = jest.fn();

    renderComponent({
      handleCancelCallback: handleCancelCallback,
    });

    fireEvent.click(screen.getByText("Cancel"));

    expect(handleCancelCallback).toHaveBeenCalledTimes(1);
  });
});
