import React from "react";
import { create } from "react-test-renderer";
import { fireEvent, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import Badge, { Props as BadgeProps } from "../../src/components/Badge";

// Make all optional for passed props so we
// only have to pass what we want to test
type PassedProps = {
  type?: "employee" | "employer" | "leave-admin";
};

const renderComponent = (passedProps: PassedProps = {}) => {
  // Prop defaults
  const props: BadgeProps = {
    // Overwrite defaults with passed props
    ...passedProps,
  };

  return render(<Badge {...props} />);
};

describe("Badge", () => {
  test("default component renders correctly", () => {
    const component = create(<Badge />).toJSON();
    expect(component).toMatchSnapshot();
  });

  test("badge renders 'Employee' text when type is `employee`", () => {
    renderComponent({
      type: "employee",
    });

    expect(screen.getByTestId("badge")).toHaveTextContent("Employee");
    expect(screen.getByTestId("badge")).toHaveClass("features-badge--employee");
  });

  test("badge renders 'Employer' text when type is `employer`", () => {
    renderComponent({
      type: "employer",
    });

    expect(screen.getByTestId("badge")).toHaveTextContent("Employer");
    expect(screen.getByTestId("badge")).toHaveClass("features-badge--employer");
  });

  test("badge renders 'Leave Admin' text when type is `leave-admin`", () => {
    renderComponent({
      type: "leave-admin",
    });

    expect(screen.getByTestId("badge")).toHaveTextContent("Leave Admin");
    expect(screen.getByTestId("badge")).toHaveClass(
      "features-badge--leave-admin",
    );
  });
});
