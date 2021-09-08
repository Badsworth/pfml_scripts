import React from "react";
import { create } from "react-test-renderer";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import Tag, { Props as TagProps } from "../../src/components/Tag";

// Make all optional for passed props so we
// only have to pass what we want to test
type PassedProps = {
  text?: string;
  color?: "green" | "blue";
};

const renderComponent = (passedProps: PassedProps = {}) => {
  // Prop defaults
  const props: TagProps = {
    text: "Test Tag",
    color: "green",
    // Overwrite defaults with passed props
    ...passedProps,
  };

  return render(<Tag {...props} />);
};

describe("Tag", () => {
  test("renders the default component", () => {
    const props: TagProps = {
      text: "Test Tag",
      color: "green",
    };

    const component = create(<Tag {...props} />).toJSON();
    expect(component).toMatchSnapshot();
  });

  test("renders with the text passed through `text` prop", () => {
    renderComponent();

    expect(screen.getByTestId("tag")).toHaveTextContent("Test Tag");
  });

  test("renders green tag when green is passed through `color` prop", () => {
    renderComponent();

    expect(screen.getByTestId("tag")).toHaveClass("tag--green");
  });

  test("renders blue tag when blue is passed through `color` prop", () => {
    renderComponent({
      color: "blue",
    });

    expect(screen.getByTestId("tag")).toHaveClass("tag--blue");
  });
});
