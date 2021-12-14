import React from "react";
import { create } from "react-test-renderer";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import Loading, { Props as LoadingProps } from "../../src/components/Loading";

// Make all optional for passed props so we
// only have to pass what we want to test
type PassedProps = {
  title?: string;
};

const renderComponent = (passedProps: PassedProps = {}) => {
  // Prop defaults
  const props: LoadingProps = {
    title: "Test loading title",
    // Overwrite defaults with passed props
    ...passedProps,
  };

  return render(<Loading {...props} />);
};

describe("Loading", () => {
  test("renders the default component", () => {
    const props: LoadingProps = {
      title: "Test loading title",
    };

    const component = create(<Loading {...props} />).toJSON();
    expect(component).toMatchSnapshot();
  });

  test("displays the title text passed through `title` prop", () => {
    renderComponent({
      title: "Test title for log in",
    });

    expect(screen.getByText("Test title for log in")).toBeInTheDocument();
    expect(
      screen.getByText(
        "This may take a few seconds, please don’t close this page.",
      ),
    ).toBeInTheDocument();
  });
});
