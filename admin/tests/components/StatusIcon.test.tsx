import React from "react";
import { create } from "react-test-renderer";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import StatusIcon, {
  Props as StatusIconProps,
} from "../../src/components/StatusIcon";

// Make all optional for passed props so we
// only have to pass what we want to test
type PassedProps = {
  status?: boolean;
};

const renderComponent = (passedProps: PassedProps = {}) => {
  // Prop defaults
  const props: StatusIconProps = {
    status: false,
    // Overwrite defaults with passed props
    ...passedProps,
  };

  return render(<StatusIcon {...props} />);
};

describe("StatusIcon", () => {
  test("renders the default component", () => {
    const props: StatusIconProps = {
      status: false,
    };

    const component = create(<StatusIcon {...props} />).toJSON();
    expect(component).toMatchSnapshot();
  });

  test("renders with disabled class when `status` prop is false", () => {
    renderComponent({
      status: false,
    });

    expect(screen.getByTestId("status-icon")).toHaveClass(
      "statusicon--disabled",
    );
  });

  test("renders with enabled class when `status` prop is true", () => {
    renderComponent({
      status: true,
    });

    expect(screen.getByTestId("status-icon")).toHaveClass(
      "statusicon--enabled",
    );
  });
});
