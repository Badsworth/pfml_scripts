import React from "react";
import { create } from "react-test-renderer";
import { fireEvent, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import Alert, { Props as AlertProps } from "../../src/components/Alert";

// Make all optional for passed props so we
// only have to pass what we want to test
type PassedProps = {
  type?: "warn" | "success" | "info" | "error" | "neutral";
  closeable?: boolean;
  children?: string;
  onClose?: Function;
};

const renderComponent = (passedProps: PassedProps = {}) => {
  // Prop defaults
  const props: AlertProps = {
    children: "This is a test alert.",
    // Overwrite defaults with passed props
    ...passedProps,
  };

  return render(<Alert {...props} />);
};

describe("Alert", () => {
  test("default component renders correctly", () => {
    const props: AlertProps = {
      children: "This is a test alert.",
    };

    const component = create(<Alert {...props} />).toJSON();
    expect(component).toMatchSnapshot();
  });

  test("renders a `warn` alert", () => {
    renderComponent({
      type: "warn",
    });

    expect(screen.getByTestId("alert-container")).toHaveClass("alert--warn");
  });

  test("renders a `success` alert", () => {
    renderComponent({
      type: "success",
    });

    expect(screen.getByTestId("alert-container")).toHaveClass("alert--success");
  });

  test("renders an `info` alert", () => {
    renderComponent({
      type: "info",
    });

    expect(screen.getByTestId("alert-container")).toHaveClass("alert--info");
  });

  test("renders an `error` alert", () => {
    renderComponent({
      type: "error",
    });

    expect(screen.getByTestId("alert-container")).toHaveClass("alert--error");
  });

  test("renders a `neutral` alert", () => {
    renderComponent({
      type: "neutral",
    });

    expect(screen.getByTestId("alert-container")).toHaveClass("alert--neutral");
  });

  test("renders an alert with the passed child text", () => {
    renderComponent({
      children: "This is a really important alert!",
    });

    expect(screen.getByTestId("alert-text")).toHaveTextContent(
      "This is a really important alert!",
    );
  });

  test("does not show the close button when `closeable` prop is set to false", () => {
    renderComponent();

    expect(screen.queryByTestId("alert-close-button")).not.toBeInTheDocument();
  });

  test("shows the close button when `closeable` prop is set to true", () => {
    renderComponent({
      closeable: true,
    });

    expect(screen.getByTestId("alert-close-button")).toBeInTheDocument();
  });

  test("removes the alert when the close button is clicked", () => {
    renderComponent({
      closeable: true,
    });

    fireEvent.click(screen.getByTestId("alert-close-button"));

    expect(screen.queryByTestId("alert-close-button")).not.toBeInTheDocument();
  });

  test("fires `onClose` callback when alert is closed", () => {
    const onClose = jest.fn();

    renderComponent({
      closeable: true,
      onClose: onClose,
    });

    fireEvent.click(screen.getByTestId("alert-close-button"));

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
