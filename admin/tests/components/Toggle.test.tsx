import React from "react";
import { create } from "react-test-renderer";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import Toggle, { Props as ToggleProps } from "../../src/components/Toggle";

// Make all optional for passed props so we
// only have to pass what we want to test
type PassedProps = {
  status?: boolean;
};

const renderComponent = (passedProps: PassedProps = {}) => {
  // Prop defaults
  const props: ToggleProps = {
    status: false,
    // Overwrite defaults with passed props
    ...passedProps,
  };

  return render(<Toggle {...props} />);
};

describe("Toggle", () => {
  test("renders the default component", () => {
    const props: ToggleProps = {
      status: false,
    };

    const component = create(<Toggle {...props} />).toJSON();
    expect(component).toMatchSnapshot();
  });

  test("renders with 'OFF' text when `status` prop is false", () => {
    renderComponent();

    expect(screen.getByTestId("toggle")).toHaveTextContent("OFF");
    expect(screen.getByTestId("toggle")).toHaveClass("toggle--off");
  });

  test("renders with 'ON' text when `status` prop is true", () => {
    renderComponent({
      status: true,
    });

    expect(screen.getByTestId("toggle")).toHaveTextContent("ON");
    expect(screen.getByTestId("toggle")).toHaveClass("toggle--on");
  });
});
