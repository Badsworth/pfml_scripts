import React from "react";
import { create } from "react-test-renderer";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import InfoRow, { Props as InfoRowProps } from "../../src/components/InfoRow";

// Make all optional for passed props so we
// only have to pass what we want to test
type PassedProps = {
  children?: React.ReactChild;
  showLogButton?: boolean;
  onClickViewLog?: Function;
};

const renderComponent = (passedProps: PassedProps = {}) => {
  // Prop defaults
  const props: InfoRowProps = {
    children: <p>Test child</p>,
    showLogButton: true,
    // Overwrite defaults with passed props
    ...passedProps,
  };

  return render(<InfoRow {...props} />);
};

describe("InfoRow", () => {
  test("renders the default component", () => {
    const props: InfoRowProps = {
      children: <p>Test child</p>,
      showLogButton: true,
    };

    const component = create(<InfoRow {...props} />).toJSON();
    expect(component).toMatchSnapshot();
  });

  test("renders 'View Log' button when `onClickViewLog` prop is passed", () => {
    const onClickViewLog = jest.fn();
    renderComponent({
      onClickViewLog: onClickViewLog,
    });

    expect(
      screen.getByRole("button", { name: "View Log" }),
    ).toBeInTheDocument();
  });

  test("fires `onClickViewLog` callback when button is clicked", () => {
    const onClickViewLog = jest.fn();
    renderComponent({
      onClickViewLog: onClickViewLog,
    });

    userEvent.click(screen.getByRole("button", { name: "View Log" }));

    expect(onClickViewLog).toHaveBeenCalled();
  });
});
